"""Vistas del Módulo 3 — Gestión de Calificaciones.

Pantallas del módulo:
- Menú según el rol (docente, alumno, secretaría/directivo).
- Docente: cargar notas, categorías, importar Excel y planilla de calificaciones.
- Boletín (RITE) del alumno y registro de firmas.
- Publicación anual del boletín (interruptor de secretaría/directivo).

Reglas de negocio:
- La calificación del cuatrimestre se pondera con el peso de las categorías.
- Valoración preliminar: TEA (7 a 10), TEP (5 a 6) o TED (0 a 4).
- La nota final aparece cuando los dos cuatrimestres tienen calificación.
- Con menos de 80 % de asistencia en una materia no se puede aprobar.
- El alumno no ve el boletín hasta que secretaría lo publica a fin de año.

El módulo solo LEE las tablas de otros módulos (alumnos, docentes,
asistencia, cuentas); todo lo que guarda vive en sus propios modelos.
"""
# --- Librería estándar -----------------------------------------------------
import importlib.util  # para saber si está instalada la librería de Excel
# Decimal = numeros exactos para notas (float tiene errores de redondeo). ROUND_HALF_UP = 7,5 redondea a 8.
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# --- Django ----------------------------------------------------------------
# messages: los carteles de "guardado" o "error" que se ven en la pantalla siguiente.
from django.contrib import messages
# Q permite armar busquedas con "O" (nombre O apellido O dni).
from django.db.models import Q
# Tipos de respuesta: HttpResponse (archivo o texto) y JsonResponse (datos para el JavaScript).
from django.http import HttpResponse, JsonResponse
# Atajos: buscar o dar 404, redirigir a otra pagina y dibujar un template.
from django.shortcuts import get_object_or_404, redirect, render
# reverse arma una URL a partir del "name" de urls.py.
from django.urls import reverse
# timezone.now() da la fecha y hora actual.
from django.utils import timezone
# Asegura que la pagina mande la cookie CSRF (la necesita el guardado automatico por JavaScript).
from django.views.decorators.csrf import ensure_csrf_cookie
# require_POST: la vista solo acepta POST (enviar datos), no entrar escribiendo la URL.
from django.views.decorators.http import require_POST

# --- Otros módulos del sistema (solo lectura) -------------------------------
# Tabla de alumnos (de otro grupo): solo se lee.
from alumnos.models import Alumno
# Registros de asistencia (de otro grupo): solo se leen.
from asistencia.models import RegistroAsistencia
# Decorador que deja entrar a una vista solo a ciertos roles.
from cuentas.decoradores import rol_requerido
# Tabla de materias (de otro grupo): solo se lee.
from docentes.models import Materia

# --- Modelos propios del módulo -------------------------------------------
# Las tablas propias del modulo (definidas en models.py).
from .models import (
    CategoriaEvaluacion,
    CierreCuatrimestre,
    ConfirmacionRite,
    NotaEvaluacion,
    PlanillaDatos,
    PublicacionBoletin,
)


# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────

# Meses de cada cuatrimestre (1° = marzo a julio, 2° = agosto a diciembre).
# Diccionario: para cada cuatrimestre, la lista de numeros de mes que abarca.
MESES_CUATRIMESTRE = {1: [3, 4, 5, 6, 7], 2: [8, 9, 10, 11, 12]}

# Roles que ven todo el módulo (planillas de todos y boletines siempre).
# Los dos roles "de gestion": secretaria (administrativo) y equipo directivo.
ROLES_GESTION = ("administrativo", "directivo")

# Asistencia mínima para aprobar una materia.
# 80 % de asistencia minima, como Decimal para poder compararlo con otros Decimal.
ASISTENCIA_MINIMA = Decimal("80")

# Nota mínima para aprobar (RITE).
# Con 7 o mas se aprueba.
NOTA_APROBACION = 7

# Importar/descargar Excel necesita la librería openpyxl. No está en
# requirements.txt (es un archivo compartido), así que se avisa si falta.
# True si la libreria openpyxl esta instalada (find_spec la busca sin importarla).
EXCEL_DISPONIBLE = importlib.util.find_spec("openpyxl") is not None


# ─────────────────────────────────────────────
#  HELPERS: ROL, CURSO Y PERMISOS
# ─────────────────────────────────────────────

# Funcion auxiliar (el "_" indica que es interna, no una pantalla). request = el pedido del navegador.
def _rol(request):
    """Rol del usuario logueado. Los superusuarios cuentan como administrativo."""
    # El superusuario (admin de Django) se trata como secretaria.
    if request.user.is_superuser:
        return "administrativo"
    # getattr con None: busca el perfil del usuario y no falla si no tiene.
    perfil = getattr(request.user, "perfil", None)
    # Devuelve el rol del perfil ("docente", "alumno", etc.) o None si no hay perfil.
    return perfil.rol if perfil is not None else None


# Devuelve la ficha del docente logueado.
def _docente_logueado(request):
    """Ficha de Docente del usuario logueado, o None si no es docente."""
    # Busca el perfil del usuario.
    perfil = getattr(request.user, "perfil", None)
    # Si no tiene perfil o no es docente, no hay ficha.
    if perfil is None or perfil.rol != "docente":
        return None
    # El perfil tiene enlazada la ficha de Docente.
    return perfil.docente


# Lee el cuatrimestre que viene en la URL como ?cuat=2.
def _cuat_de_query(request):
    """Cuatrimestre elegido con ?cuat= (1 o 2). Si viene mal, usa el 1°."""
    # try/except: intenta convertir a numero y, si falla, no rompe la pagina.
    try:
        # request.GET son los datos de la URL; si no viene "cuat" usa 1.
        cuat = int(request.GET.get("cuat", 1))
    # Si el valor no era un numero...
    except (TypeError, ValueError):
        # ...devuelve el 1° cuatrimestre.
        return 1
    # Solo acepta 1 o 2; cualquier otro numero se vuelve 1.
    return cuat if cuat in (1, 2) else 1


# Arma el texto del curso para mostrar.
def _texto_curso(curso):
    """'5° B' a partir de un Curso."""
    # f-string: mete las variables dentro del texto.
    return f"{curso.anio}° {curso.division}"


# Devuelve los alumnos de un curso.
def _alumnos_del_curso(curso):
    """Alumnos activos de un curso, ordenados por apellido.

    El módulo Alumnos guarda el año y la división en cada alumno (no hay
    relación directa con Curso), así que se filtra por esos dos campos.
    """
    # Filtra alumnos por año y division del curso y que esten activos...
    return Alumno.objects.filter(
        anio=curso.anio, division=curso.division, activo=True,
    # ...ordenados alfabeticamente por apellido y nombre.
    ).order_by("apellido", "nombre")


# Devuelve las materias que cursa un alumno.
def _materias_del_alumno(alumno):
    """Materias del curso del alumno (mismo año y división)."""
    # curso__anio = "el año del curso de la materia" (el __ cruza a la tabla Curso).
    return Materia.objects.filter(
        curso__anio=alumno.anio, curso__division=alumno.division,
    # select_related trae curso y docente en la misma consulta (mas rapido).
    ).select_related("curso", "docente").order_by("nombre")


# Chequeo de seguridad: verifica que el alumno sea de ese curso.
def _alumno_de_la_materia(materia, alumno_id):
    """Alumno activo del curso de la materia, o None si no pertenece a ese curso."""
    # .first() devuelve el primero o None si no hay ninguno.
    return _alumnos_del_curso(materia.curso).filter(id=alumno_id).first()


# PERMISO DE LECTURA: decide si el usuario puede ver una materia.
def _materia_para_consulta(request, materia_id):
    """Materia que el usuario puede VER, o None.

    - El docente solo ve sus materias.
    - Secretaría y directivo ven las de todos (para imprimir planillas).
    """
    # Busca la materia por id (con su curso y docente).
    materia = (
        Materia.objects.select_related("curso", "docente")
        .filter(id=materia_id).first()
    )
    # Si no existe, no hay nada que ver.
    if materia is None:
        return None
    # Secretaria y directivo pueden ver cualquier materia.
    if _rol(request) in ROLES_GESTION:
        return materia
    # Si no es de gestion, se fija si es docente...
    docente = _docente_logueado(request)
    # ...y si es EL docente de esa materia.
    if docente is not None and materia.docente_id == docente.id:
        return materia
    # Cualquier otro caso: sin permiso.
    return None


# PERMISO DE ESCRITURA: solo el docente dueño de la materia puede modificar.
def _materia_del_docente(request, materia_id):
    """Materia que el usuario puede MODIFICAR: solo el docente que la da."""
    # Ficha del docente logueado.
    docente = _docente_logueado(request)
    # Si no es docente, no puede modificar nada.
    if docente is None:
        return None
    # Busca la materia SOLO entre las de ese docente; si no es suya devuelve None.
    return (
        Materia.objects.select_related("curso", "docente")
        .filter(id=materia_id, docente=docente).first()
    )


# Nombre del docente para los encabezados.
def _nombre_docente(materia):
    """Nombre y apellido del docente de la materia, o '—' si no tiene."""
    # Docente de la materia (puede no tener).
    docente = materia.docente
    # Si no tiene docente asignado muestra una raya.
    if docente is None:
        return "—"
    # Nombre completo; si esta vacio usa el DNI.
    return f"{docente.nombre} {docente.apellido}".strip() or docente.dni


# Devuelve las columnas de la grilla de una materia.
def _categorias(materia):
    """Categorías de evaluación de la materia, en el orden de la grilla."""
    # list(...) convierte la consulta en una lista comun de Python.
    return list(
        # Categorias de esta materia...
        CategoriaEvaluacion.objects.filter(materia=materia)
        # ...ordenadas...
        .order_by("orden", "nombre")
        # ...y como diccionarios con solo estos campos (.values).
        .values("id", "nombre", "orden", "grupo", "peso")
    )


# ─────────────────────────────────────────────
#  HELPERS: PUBLICACIÓN DEL BOLETÍN
# ─────────────────────────────────────────────

# Dice si el boletin de un año esta publicado.
def _boletin_publicado(anio=None):
    """True si secretaría publicó el boletín del año (por defecto, el actual)."""
    # Si no se paso un año, usa el actual.
    anio = anio or timezone.now().year
    # .exists() devuelve True/False sin traer los datos.
    return PublicacionBoletin.objects.filter(anio=anio, publicado=True).exists()


# Regla de quien puede ver el boletin.
def _puede_ver_boletin(request):
    """Secretaría y directivo siempre; alumno y docente solo con el año publicado."""
    # Gestion siempre; los demas solo si esta publicado.
    return _rol(request) in ROLES_GESTION or _boletin_publicado()


# ─────────────────────────────────────────────
#  HELPERS: NÚMEROS Y FORMATO
# ─────────────────────────────────────────────

# Redondea un numero a N decimales.
def _redondear(valor, decimales=2):
    """Redondea un Decimal (la mitad hacia arriba, como en la escuela)."""
    # quantize redondea; ROUND_HALF_UP hace que la mitad suba (7,5 -> 8).
    return valor.quantize(Decimal("1").scaleb(-decimales), rounding=ROUND_HALF_UP)


# Saca los ceros de mas de un numero.
def _num_limpio(valor):
    """Decimal como texto con punto y sin ceros de más: 8.50 -> '8.5'."""
    # Si no hay valor, devuelve None.
    if valor is None:
        return None
    # Lo pasa a texto.
    texto = str(valor)
    # Si tiene decimales...
    if "." in texto:
        # ...quita los ceros finales y el punto si quedo colgando ("8.50" -> "8.5", "8.0" -> "8").
        texto = texto.rstrip("0").rstrip(".")
    return texto


# Cambia el punto por coma para mostrar como en Argentina.
def _formato_ar(valor):
    """Decimal con coma decimal (formato argentino): 8.5 -> '8,5'."""
    return None if valor is None else _num_limpio(valor).replace(".", ",")


# Convierte lo que escribe el usuario en un numero valido (o None).
def _decimal_desde_texto(texto, minimo=None, maximo=None):
    """Convierte lo que escribe el usuario ('7,5', '8') a Decimal.

    Acepta coma o punto. Devuelve None si está vacío, no es un número o
    queda fuera del rango [minimo, maximo].
    """
    # Limpia espacios y cambia coma por punto.
    texto = str(texto if texto is not None else "").strip().replace(",", ".")
    # Vacio = sin valor.
    if not texto:
        return None
    # Intenta convertirlo a Decimal...
    try:
        valor = Decimal(texto)
    # ...y si no es un numero (ej. "abc") devuelve None.
    except InvalidOperation:
        return None
    # Rechaza valores raros como infinito o NaN.
    if not valor.is_finite():
        return None
    # Rechaza si es menor al minimo permitido.
    if minimo is not None and valor < minimo:
        return None
    # Rechaza si supera el maximo.
    if maximo is not None and valor > maximo:
        return None
    # Si paso todos los controles, devuelve el numero.
    return valor


# Valida una nota: tiene que estar entre 0 y 10.
def _nota_desde_texto(texto):
    """Nota de 0 a 10, o None."""
    return _decimal_desde_texto(texto, minimo=Decimal("0"), maximo=Decimal("10"))


# ─────────────────────────────────────────────
#  HELPERS: CÁLCULO DE CALIFICACIONES
# ─────────────────────────────────────────────

# Junta las columnas que comparten "grupo" (ej. TP1 y TP2 dentro de "Trabajos practicos").
def _grupos_de_categorias(categorias):
    """Agrupa categorías seguidas que comparten 'grupo' (ej. 'Trabajos prácticos').

    Cada grupo queda como {nombre, peso, cats}. Una categoría sin grupo es
    un grupo de una sola columna. El peso del grupo es la suma de los pesos
    de sus categorías (o None si ninguna tiene peso).
    """
    # Lista donde se van armando los grupos.
    grupos = []
    # Recorre las categorias en orden.
    for cat in categorias:
        # Nombre del grupo de esta categoria ("" si no tiene).
        nombre = cat.get("grupo") or ""
        # Si el ultimo grupo armado tiene el mismo nombre, la categoria se suma a ese grupo...
        if grupos and nombre and grupos[-1]["nombre"] == nombre:
            # ...agregandola a su lista.
            grupos[-1]["cats"].append(cat)
        # Si no, se abre un grupo nuevo.
        else:
            grupos.append({"nombre": nombre, "cats": [cat]})
    # Segunda pasada: calcula el peso de cada grupo.
    for grupo in grupos:
        # Pesos de las categorias del grupo que tienen peso.
        pesos = [c["peso"] for c in grupo["cats"] if c["peso"] is not None]
        # El peso del grupo es la suma (o None si ninguna tiene).
        grupo["peso"] = sum(pesos) if pesos else None
    return grupos


# CALCULO PRINCIPAL: nota del cuatrimestre a partir de las notas cargadas.
def _calificacion_cuat(notas, categorias):
    """Calificación del cuatrimestre (Decimal con 1 decimal) o None si no hay notas.

    notas = {categoria_id: Decimal}.
    - Sin pesos: promedio simple de las notas cargadas.
    - Con pesos: cada grupo aporta su peso; dentro del grupo, las notas que
      faltan no cuentan (se promedian las cargadas).
    """
    # Notas que realmente estan cargadas (saltea las vacias).
    presentes = [notas[c["id"]] for c in categorias if notas.get(c["id"]) is not None]
    # Sin notas no hay calificacion.
    if not presentes:
        return None

    # Si NINGUNA categoria tiene peso...
    if not any(c.get("peso") is not None for c in categorias):
        # ...promedio simple: suma / cantidad, con 1 decimal.
        return _redondear(sum(presentes, Decimal("0")) / len(presentes), 1)

    # Con pesos: acumulado suma (promedio del grupo x peso).
    acumulado = Decimal("0")
    # Suma de los pesos usados, para dividir al final.
    peso_total = Decimal("0")
    # Recorre cada grupo de columnas.
    for grupo in _grupos_de_categorias(categorias):
        # Pares (categoria, nota) del grupo que tienen nota.
        con_nota = [(c, notas[c["id"]]) for c in grupo["cats"] if notas.get(c["id"]) is not None]
        # Si el grupo no tiene ninguna nota, no cuenta.
        if not con_nota:
            continue
        # Peso de cada categoria con nota (1 si no tiene peso).
        pesos = [c["peso"] if c["peso"] is not None else Decimal("1") for c, _ in con_nota]
        # Promedio ponderado dentro del grupo: suma(nota x peso) / suma(pesos).
        promedio_grupo = sum(n * p for (_, n), p in zip(con_nota, pesos)) / sum(pesos)
        # Peso del grupo (si no tiene, la cantidad de columnas).
        peso_grupo = grupo["peso"] if grupo["peso"] is not None else Decimal(len(grupo["cats"]))
        # Suma lo que aporta este grupo.
        acumulado += promedio_grupo * peso_grupo
        # Suma el peso usado.
        peso_total += peso_grupo

    # Evita dividir por cero.
    if peso_total == 0:
        return None
    # Promedio ponderado final con 1 decimal.
    return _redondear(acumulado / peso_total, 1)


# Igual que la anterior pero redondeada a numero entero (lo que va al boletin).
def _calificacion_entera(notas, categorias):
    """Calificación del cuatrimestre redondeada a entero (escala 1 a 10), o None."""
    # Calcula la nota con 1 decimal.
    calif = _calificacion_cuat(notas, categorias)
    # La redondea a entero si existe.
    return _redondear(calif, 0) if calif is not None else None


# Convierte la nota en valoracion RITE.
def _valoracion_preliminar(nota):
    """TEA (7 o más), TEP (5 a 6) o TED (menos de 5) a partir de la nota."""
    # Sin nota no hay valoracion.
    if nota is None:
        return ""
    # 7 o mas: Trayectoria Avanzada.
    if nota >= 7:
        return "TEA"
    # 5 o 6: En Proceso.
    if nota >= 5:
        return "TEP"
    # Menos de 5: Discontinua.
    return "TED"


# Texto del estado de la materia.
def _estado_materia(nota, asistencia_ok=True):
    """Texto del estado: 'Aprobada', 'A intensificar' o 'No acredita por asistencia'."""
    # Sin nota no hay estado.
    if nota is None:
        return None
    # Si no llego al 80 % de asistencia no acredita, tenga la nota que tenga.
    if not asistencia_ok:
        return "No acredita por asistencia"
    # 7 o mas aprueba; si no, va a intensificar.
    return "Aprobada" if nota >= NOTA_APROBACION else "A intensificar"


# Arma el resumen de un cuatrimestre para mostrar en planilla, boletin y "Mis notas".
def _datos_cuatrimestre(notas, categorias, cierre):
    """Datos de un cuatrimestre: notas por columna, valoración y calificación.

    Si el docente ya cerró el cuatrimestre, manda la calificación del cierre.
    Si eligió una valoración a mano, manda esa; si no, se deriva de la nota.
    """
    # Nota entera calculada con las notas cargadas.
    calif = _calificacion_entera(notas, categorias)
    # Si el cuatrimestre ya se cerro y quedo una nota oficial guardada...
    if cierre is not None and cierre.calificacion is not None:
        # ...manda esa nota guardada (no la recalculada).
        calif = _redondear(cierre.calificacion, 0)

    # Si el docente eligio la valoracion a mano, se respeta.
    if cierre is not None and cierre.valoracion_preliminar:
        valoracion = cierre.valoracion_preliminar
    # Si no la eligio...
    else:
        # ...se deduce de la nota (TEA/TEP/TED).
        valoracion = _valoracion_preliminar(calif)

    # Devuelve un diccionario listo para el template.
    return {
        # Lista con la nota de cada columna, en orden ("" donde no hay nota).
        "valores": [_num_limpio(notas.get(c["id"])) or "" for c in categorias],
        # TEA / TEP / TED.
        "valoracion": valoracion,
        # La calificacion como texto ("" si no hay).
        "calificacion": str(calif) if calif is not None else "",
        # True si tiene 7 o mas.
        "aprobada": calif is not None and calif >= NOTA_APROBACION,
        # True si hay calificacion.
        "tiene_calificacion": calif is not None,
    }


# Nota final automatica del año = promedio de los dos cuatrimestres.
def _final_automatico(d1, d2, cierre1):
    """Promedio entero del 1° cuatrimestre (o su intensificación) y el 2°.

    Devuelve '' si todavía falta la calificación de alguno de los dos.
    """
    # Si falta la nota de alguno de los dos, todavia no hay final.
    if not d1["calificacion"] or not d2["calificacion"]:
        return ""
    # Nota del 1° cuatrimestre.
    nota1 = Decimal(d1["calificacion"])
    # Si intensifico el 1° y tiene nota de intensificacion...
    if cierre1 is not None and cierre1.intensificacion and cierre1.calificacion_final is not None:
        # ...esa nota reemplaza a la del 1° cuatrimestre.
        nota1 = cierre1.calificacion_final
    # Nota del 2° cuatrimestre.
    nota2 = Decimal(d2["calificacion"])
    # Promedio de las dos, redondeado a entero.
    return _num_limpio(_redondear((nota1 + nota2) / 2, 0))


# Decide que nota final se muestra.
def _calificacion_final(d1, d2, cierre1, cierre2):
    """Nota final del año: la que cargó el docente a mano o, si no hay, la automática."""
    # Si el docente escribio la final a mano (se guarda en el cierre del 2° cuat.)...
    if cierre2 is not None and cierre2.calificacion_final is not None:
        # ...manda esa.
        return _num_limpio(cierre2.calificacion_final)
    # Si no, la calculada automaticamente.
    return _final_automatico(d1, d2, cierre1)


# Devuelve la nota de intensificacion del 1° cuatrimestre.
def _intensificacion(cierre1):
    """Nota de intensificación del 1° cuatrimestre (texto) o ''."""
    # Solo si esta marcada la intensificacion y tiene nota.
    if cierre1 is not None and cierre1.intensificacion and cierre1.calificacion_final is not None:
        return _num_limpio(cierre1.calificacion_final)
    # Si no, vacio.
    return ""


# ─────────────────────────────────────────────
#  HELPERS: ASISTENCIA (se lee del módulo Asistencia)
# ─────────────────────────────────────────────

# Cuenta faltas: ausente vale 1 y tardanza vale media.
def _faltas(registros):
    """Faltas de un conjunto de registros: Ausente = 1 y Tardanza = 0,5."""
    # Cantidad de registros con estado "A" (ausente).
    ausentes = registros.filter(estado="A").count()
    # Cantidad con estado "T" (tardanza).
    tardanzas = registros.filter(estado="T").count()
    # Total = ausentes + tardanzas / 2.
    return Decimal(ausentes) + Decimal(tardanzas) / 2


# Faltas del alumno en todo el cuatrimestre (sumando todas las materias).
def _inasistencias_alumno_cuat(alumno, cuat):
    """Inasistencias totales del alumno en el cuatrimestre (todas las materias)."""
    # Registros de asistencia del alumno cuyo mes cae en el cuatrimestre (fecha__month__in).
    registros = RegistroAsistencia.objects.filter(
        alumno=alumno, fecha__month__in=MESES_CUATRIMESTRE[cuat],
    )
    # Cuenta las faltas y redondea.
    return _redondear(_faltas(registros))


# Faltas del alumno en una sola materia y cuatrimestre.
def _inasistencias_materia_cuat(alumno_id, materia, cuat):
    """Inasistencias del alumno en UNA materia y un cuatrimestre."""
    # Igual que arriba pero filtrando tambien por materia.
    registros = RegistroAsistencia.objects.filter(
        alumno_id=alumno_id, materia=materia, fecha__month__in=MESES_CUATRIMESTRE[cuat],
    )
    return _redondear(_faltas(registros))


# Calcula el % de asistencia anual en una materia (regla del 80 %).
def _asistencia_materia(alumno_id, materia):
    """Asistencia anual del alumno en una materia, o None si no hay registros.

    Total de clases = fechas distintas con algún registro de la materia.
    Devuelve {clases, faltas, porcentaje, suficiente}; 'suficiente' es la
    regla del 80 %: sin eso la materia no se aprueba.
    """
    # Todos los registros de asistencia de la materia.
    registros = RegistroAsistencia.objects.filter(materia=materia)
    # Clases dadas = cantidad de fechas distintas en que se tomo asistencia.
    clases = registros.values("fecha").distinct().count()
    # Si nunca se tomo asistencia, no se puede calcular.
    if not clases:
        return None
    # Faltas de este alumno en la materia.
    faltas = _faltas(registros.filter(alumno_id=alumno_id))
    # Porcentaje = (clases - faltas) / clases x 100.
    porcentaje = _redondear((clases - faltas) / clases * 100, 1)
    # Devuelve los datos de asistencia.
    return {
        "clases": clases,
        "faltas": _redondear(faltas, 1),
        "porcentaje": porcentaje,
        # True si llega al 80 %.
        "suficiente": porcentaje >= ASISTENCIA_MINIMA,
    }


# Cantidad de clases dadas en un cuatrimestre.
def _clases_dadas(materia, cuat):
    """Clases efectivamente dadas en el cuatrimestre (días con asistencia tomada)."""
    # Dias distintos con asistencia tomada en los meses del cuatrimestre.
    return RegistroAsistencia.objects.filter(
        materia=materia, fecha__month__in=MESES_CUATRIMESTRE[cuat],
    ).values("fecha").distinct().count()


# ─────────────────────────────────────────────
#  HELPERS: CIERRE DEL CUATRIMESTRE (uno por materia)
# ─────────────────────────────────────────────

# Dice si el cuatrimestre de una materia esta cerrado y desde cuando.
def _fecha_cierre(materia, cuat):
    """Fecha de cierre ('30/07/2026') si el cuatrimestre de la materia está cerrado.

    Devuelve None si sigue abierto. Mientras está cerrado no se pueden cambiar
    las notas: el docente lo reabre desde la planilla si necesita corregir.
    """
    # Cierres de esa materia y cuatrimestre marcados como cerrados.
    cerrados = CierreCuatrimestre.objects.filter(materia=materia, cuatrimestre=cuat, cerrado=True)
    # Si no hay ninguno, sigue abierto.
    if not cerrados.exists():
        return None
    # Toma el cierre mas reciente que tenga fecha.
    ultimo = cerrados.exclude(fecha_cierre=None).order_by("-fecha_cierre").first()
    # Devuelve la fecha como dia/mes/año (hora local) o "sin fecha".
    return timezone.localtime(ultimo.fecha_cierre).strftime("%d/%m/%Y") if ultimo else "sin fecha"


# Texto del aviso de cuatrimestre cerrado.
def _aviso_cerrado(cuat):
    """Mensaje que se muestra cuando se intenta cambiar un cuatrimestre cerrado."""
    return f"El {cuat}° cuatrimestre está cerrado. Para cambiar notas, reabrilo desde la planilla."


# ─────────────────────────────────────────────
#  MENÚ Y PUBLICACIÓN ANUAL DEL BOLETÍN
# ─────────────────────────────────────────────

# Solo entran usuarios logueados con alguno de estos roles.
@rol_requerido("alumno", "docente", "administrativo", "directivo")
# VISTA: pantalla de inicio del modulo. Muestra algo distinto segun el rol.
def menu(request):
    """Inicio del módulo: cada rol ve su propia pantalla."""
    # Cuatrimestre elegido en la URL (?cuat=).
    cuat = _cuat_de_query(request)
    # Año actual.
    anio = timezone.now().year
    # contexto = los datos que se le pasan al template.
    contexto = {
        "cuat": cuat,
        "ciclo_lectivo": anio,
        # Si el boletin de este año ya esta publicado.
        "boletin_publicado": _boletin_publicado(anio),
    }

    # Perfil del usuario (dice su rol y a que alumno/docente corresponde).
    perfil = getattr(request.user, "perfil", None)
    # Rol del usuario.
    rol = _rol(request)

    # Si es docente y tiene ficha de docente...
    if rol == "docente" and perfil.docente is not None:
        # ...agrega sus materias al contexto...
        contexto.update(_datos_menu_docente(perfil.docente, cuat))
        # ...y muestra el menu del docente.
        return render(request, "calificaciones/menu_docente.html", contexto)

    # Si es alumno y tiene ficha de alumno...
    if rol == "alumno" and perfil.alumno is not None:
        # ...agrega su resumen "Mis notas"...
        contexto.update(_datos_menu_alumno(perfil.alumno, cuat))
        # ...y muestra el menu del alumno.
        return render(request, "calificaciones/menu_alumno.html", contexto)

    # Secretaría, directivo y superusuarios.
    # Para gestion: la lista de todas las materias.
    contexto.update(_datos_menu_gestion())
    # Solo gestion ve el boton de publicar boletines.
    contexto["puede_publicar_boletin"] = rol in ROLES_GESTION
    # Muestra el menu de gestion.
    return render(request, "calificaciones/menu.html", contexto)


# Solo secretaria y directivo.
@rol_requerido("administrativo", "directivo")
# Solo por POST (apretando el boton del formulario).
@require_POST
# VISTA: prende o apaga la publicacion del boletin del año.
def publicar_boletines(request):
    """Interruptor anual: publica u oculta el boletín de este año."""
    # Año actual.
    anio = timezone.now().year
    # Busca el registro del año y, si no existe, lo crea (el _ descarta el "fue creado").
    publicacion, _ = PublicacionBoletin.objects.get_or_create(anio=anio)
    # Invierte el valor: si estaba publicado lo oculta y al reves.
    publicacion.publicado = not publicacion.publicado
    # Guarda la fecha si quedo publicado; la borra si quedo oculto.
    publicacion.fecha_publicacion = timezone.now() if publicacion.publicado else None
    # Guarda quien lo hizo.
    publicacion.usuario = request.user.get_username()
    # Graba en la base de datos.
    publicacion.save()

    # Cartel distinto segun como quedo.
    if publicacion.publicado:
        messages.success(request, f"Boletines {anio} publicados. Los alumnos ya pueden ver su boletín.")
    else:
        messages.success(request, f"Boletines {anio} ocultos. Los alumnos ven solo su resumen de notas.")
    # Vuelve al menu (patron POST -> redirect, para que F5 no repita la accion).
    return redirect("calificaciones_menu")


# Datos del menu de gestion.
def _datos_menu_gestion():
    """Todas las materias con su docente, para ver o imprimir cada planilla."""
    # Todas las materias con su docente y curso...
    materias = (
        Materia.objects.select_related("docente", "curso")
        # ...ordenadas por apellido del docente.
        .order_by("docente__apellido", "docente__nombre", "nombre")
    )
    # Devuelve una lista de diccionarios, uno por materia (lista por comprension).
    return {
        "materias_todas": [
            {
                "id": m.id,
                "nombre": m.nombre,
                "curso": _texto_curso(m.curso),
                "docente": _nombre_docente(m),
            }
            for m in materias
        ],
    }


# Datos del menu del docente: sus materias y cuanto cargo en cada una.
def _datos_menu_docente(docente, cuat):
    """Materias del docente con el porcentaje de notas cargadas en el cuatrimestre."""
    # Materias que da este docente.
    materias = (
        Materia.objects.filter(docente=docente)
        .select_related("curso")
        .order_by("nombre", "curso__anio", "curso__division")
    )

    # Una fila por materia.
    filas = []
    # Recorre las materias.
    for m in materias:
        # Cantidad de alumnos del curso.
        cant_alumnos = _alumnos_del_curso(m.curso).count()
        # Cantidad de columnas (categorias) de la materia.
        cant_categorias = CategoriaEvaluacion.objects.filter(materia=m).count()
        esperadas = cant_alumnos * cant_categorias  # una nota por alumno y categoría

        # Porcentaje de carga (None si no hay nada que cargar).
        pct = None
        # Solo si hay notas esperadas (evita dividir por cero).
        if esperadas:
            # Cuenta cuantos pares alumno-categoria distintos ya tienen nota.
            cargadas = (
                NotaEvaluacion.objects.filter(materia=m, cuatrimestre=cuat)
                .values("alumno_id", "categoria_id").distinct().count()
            )
            # Porcentaje cargado, con tope en 100.
            pct = min(100, int(cargadas * 100 / esperadas))

        # Agrega la fila de esta materia.
        filas.append({
            "id": m.id,
            "nombre": m.nombre,
            "curso": _texto_curso(m.curso),
            "estudiantes": cant_alumnos,
            "pct": pct,
            # True si esta todo cargado.
            "completo": pct == 100,
            "fecha_cierre": _fecha_cierre(m, cuat),  # None = cuatrimestre abierto
        })

    # Datos para el template, con los totales de las tarjetas de arriba.
    return {
        "materias": filas,
        "total_materias": len(filas),
        # Materias que todavia no estan completas.
        "sin_cargar": sum(1 for f in filas if not f["completo"]),
        # Materias con el cuatrimestre cerrado.
        "cerradas": sum(1 for f in filas if f["fecha_cierre"]),
        # Para mostrar u ocultar los botones de Excel.
        "excel_disponible": EXCEL_DISPONIBLE,
    }


# Datos de "Mis notas" del alumno.
def _datos_menu_alumno(alumno, cuat):
    """'Mis notas': calificación, valoración y estado de cada materia del alumno."""
    # Diccionario {id de materia: cierre} del alumno en este cuatrimestre.
    cierres = {
        c.materia_id: c
        for c in CierreCuatrimestre.objects.filter(alumno=alumno, cuatrimestre=cuat)
    }

    # Filas de la tabla.
    filas = []
    # Notas para el promedio general.
    calificaciones = []
    # Recorre las materias del curso del alumno.
    for materia in _materias_del_alumno(alumno):
        # Diccionario {id de categoria: nota} del alumno en esta materia.
        notas = {
            n.categoria_id: n.valor
            for n in NotaEvaluacion.objects.filter(alumno=alumno, materia=materia, cuatrimestre=cuat)
        }
        # Resumen del cuatrimestre (nota, valoracion, etc.).
        datos = _datos_cuatrimestre(notas, _categorias(materia), cierres.get(materia.id))
        # La calificacion como numero (o None).
        calif = Decimal(datos["calificacion"]) if datos["calificacion"] else None
        # Si tiene nota, se guarda para el promedio.
        if calif is not None:
            calificaciones.append(calif)

        # Asistencia anual en la materia.
        asistencia = _asistencia_materia(alumno.id, materia)
        # Esta OK si no hay registros de asistencia o si llega al 80 %.
        asistencia_ok = asistencia is None or asistencia["suficiente"]

        # Fila de esta materia.
        filas.append({
            "materia": materia.nombre,
            "valoracion": datos["valoracion"],
            "calificacion": datos["calificacion"],
            # "Aprobada", "A intensificar" o "No acredita por asistencia".
            "estado": _estado_materia(calif, asistencia_ok),
            # Aprobada solo si tiene la nota Y la asistencia.
            "aprobada": datos["aprobada"] and asistencia_ok,
        })

    # Promedio general (None si no hay notas).
    promedio = None
    if calificaciones:
        # Promedio con 1 decimal y coma argentina.
        promedio = _formato_ar(_redondear(sum(calificaciones) / len(calificaciones), 1))

    # Datos para el template.
    return {
        "nombre": f"{alumno.apellido}, {alumno.nombre}",
        "curso": f"{alumno.anio}° {alumno.division}",
        "materias": filas,
        "promedio_general": promedio,
        # Faltas totales del cuatrimestre.
        "inasistencias": _formato_ar(_inasistencias_alumno_cuat(alumno, cuat)),
    }


# ─────────────────────────────────────────────
#  BOLETÍN (RITE)
# ─────────────────────────────────────────────

# Entran docentes, secretaria y directivo (los alumnos no).
@rol_requerido("docente", "administrativo", "directivo")
# VISTA: buscador para elegir de que alumno ver el boletin.
def alumno_seleccionar(request):
    """Buscador de alumno para abrir su boletín (el docente ve solo sus cursos)."""
    # Alumnos que este usuario tiene permitido ver, ordenados por curso y apellido.
    alumnos = _alumnos_que_puede_ver(request).order_by("anio", "division", "apellido", "nombre")
    # Muestra la pantalla con la lista.
    return render(request, "calificaciones/alumno_seleccionar.html", {
        "alumnos": alumnos,
        "boletin_publicado": _boletin_publicado(),
        "puede_ver": _puede_ver_boletin(request),
    })


# Devuelve los alumnos que el usuario puede consultar.
def _alumnos_que_puede_ver(request):
    """Alumnos cuyo boletín puede abrir el usuario.

    Secretaría y directivo: todos. Docente: solo los de los cursos donde da
    alguna materia.
    """
    # Arranca con todos los alumnos activos.
    alumnos = Alumno.objects.filter(activo=True)
    # Si no es docente (o sea, gestion), los ve a todos.
    if _rol(request) != "docente":
        return alumnos
    # Ficha del docente.
    docente = _docente_logueado(request)
    # Pares (año, division) de los cursos donde da clases, sin repetir.
    cursos = Materia.objects.filter(docente=docente).values_list("curso__anio", "curso__division").distinct()
    filtro = Q(pk__in=[])  # arranca sin ningún alumno
    # Por cada curso suyo...
    for anio, division in cursos:
        # ...agrega "O es de este año y division" al filtro ( |= es un "o").
        filtro |= Q(anio=anio, division=division)
    # Devuelve solo los alumnos de esos cursos.
    return alumnos.filter(filtro)


# Decide de que alumno se muestra el boletin (y evita que un alumno vea el de otro).
def _alumno_a_mostrar(request):
    """El alumno ve SIEMPRE su propio boletín; los demás roles eligen con alumno_id."""
    # Perfil del usuario.
    perfil = getattr(request.user, "perfil", None)
    # Si el usuario es alumno...
    if perfil is not None and perfil.rol == "alumno":
        # ...siempre es su propia ficha: ignora cualquier alumno_id que venga en la URL.
        return perfil.alumno
    # Los demas roles mandan el id del alumno por formulario (POST) o por la URL (GET).
    alumno_id = request.POST.get("alumno_id") or request.GET.get("alumno_id")
    # Si no vino o no es un numero, no hay alumno.
    if not alumno_id or not str(alumno_id).isdigit():
        return None
    # Lo busca SOLO entre los alumnos que el usuario puede ver.
    alumno = _alumnos_que_puede_ver(request).filter(id=alumno_id).first()
    # Si no esta entre los permitidos...
    if alumno is None:
        # ...muestra un error.
        messages.error(request, "Solo podés ver el boletín de alumnos de tus cursos.")
    return alumno


# Regla de quien puede registrar cada firma del boletin.
def _puede_firmar(request, tipo):
    """Quién registra cada firma del boletín.

    - Estudiante: el propio alumno.
    - Adulta/o responsable: el docente del curso, secretaría o directivo.
    - Director/a: solo el equipo directivo.
    """
    # Rol del usuario.
    rol = _rol(request)
    # La firma del estudiante...
    if tipo == "estudiante":
        # ...solo la pone el alumno.
        return rol == "alumno"
    # La firma del director...
    if tipo == "director":
        # ...solo el equipo directivo (o el superusuario).
        return rol == "directivo" or request.user.is_superuser
    # La del adulto responsable la registra el personal de la escuela.
    return rol in ("docente", "administrativo", "directivo")


# Arma TODOS los datos del boletin (RITE) de un alumno.
def _datos_rite(alumno, request):
    """Datos del boletín: frente (calificaciones) y dorso (intensificación,
    asistencia y firmas)."""
    notas = {}  # {(materia_id, cuat): {categoria_id: valor}}
    # Recorre todas las notas del alumno...
    for n in NotaEvaluacion.objects.filter(alumno=alumno).order_by("id"):
        # ...y las agrupa por (materia, cuatrimestre). setdefault crea el diccionario si no existia.
        notas.setdefault((n.materia_id, n.cuatrimestre), {})[n.categoria_id] = n.valor
    # Cierres del alumno, con clave (materia, cuatrimestre).
    cierres = {
        (c.materia_id, c.cuatrimestre): c
        for c in CierreCuatrimestre.objects.filter(alumno=alumno)
    }

    # Materias del curso del alumno.
    materias = list(_materias_del_alumno(alumno))
    # Renglones del frente del boletin.
    filas = []
    # Materias que intensifica (van al dorso).
    intensifican = []
    # Recorre cada materia.
    for m in materias:
        # Columnas de la materia.
        categorias = _categorias(m)
        # Cierre del 1° cuatrimestre (None si no hay).
        cierre1 = cierres.get((m.id, 1))
        # Cierre del 2° cuatrimestre.
        cierre2 = cierres.get((m.id, 2))
        # Resumen del 1° cuatrimestre.
        d1 = _datos_cuatrimestre(notas.get((m.id, 1), {}), categorias, cierre1)
        # Resumen del 2° cuatrimestre.
        d2 = _datos_cuatrimestre(notas.get((m.id, 2), {}), categorias, cierre2)

        # Asistencia anual en la materia.
        asistencia = _asistencia_materia(alumno.id, m)
        # OK si no hay registros o si llega al 80 %.
        asistencia_ok = asistencia is None or asistencia["suficiente"]

        # Promedio anual: solo si los dos cuatrimestres están aprobados y la
        # asistencia alcanza.
        # Empieza vacio.
        promedio_anual = ""
        # Solo si tiene asistencia y aprobo los dos cuatrimestres...
        if asistencia_ok and d1["aprobada"] and d2["aprobada"]:
            # ...suma las dos notas...
            suma = Decimal(d1["calificacion"]) + Decimal(d2["calificacion"])
            # ...y saca el promedio con 1 decimal.
            promedio_anual = _formato_ar(_redondear(suma / 2, 1))

        # Renglon de la materia en el boletin.
        filas.append({
            "materia": m.nombre,
            "anio": f"{m.curso.anio}°",
            # C o R (por defecto C).
            "cursada": cierre1.cursada if cierre1 else "C",
            # Valoracion y nota del 1° cuatrimestre.
            "val1": d1["valoracion"],
            "calif1": d1["calificacion"],
            # Valoracion y nota del 2° cuatrimestre.
            "val2": d2["valoracion"],
            "calif2": d2["calificacion"],
            "promedio_anual": promedio_anual,
            # Nota de intensificacion del 1° cuatrimestre.
            "intensificacion": _intensificacion(cierre1),
            # Nota de diciembre (si la tiene).
            "dic": _num_limpio(cierre2.nota_diciembre) if cierre2 and cierre2.nota_diciembre is not None else "",
            # Nota de febrero (si la tiene).
            "feb": _num_limpio(cierre2.nota_febrero) if cierre2 and cierre2.nota_febrero is not None else "",
            # True si no llego al 80 % de asistencia.
            "no_acredita": not asistencia_ok,
        })

        # Si tiene que intensificar (y la asistencia alcanza)...
        if cierre1 is not None and cierre1.intensificacion and asistencia_ok:
            # ...se agrega a la lista del dorso.
            intensifican.append({
                "materia": m.nombre,
                "anio": f"{m.curso.anio}°",
                "calif_final": _num_limpio(cierre1.calificacion_final) or "",
            })

    # El dorso oficial tiene 9 renglones de intensificación.
    # Completa con renglones vacios hasta llegar a 9.
    while len(intensifican) < 9:
        intensifican.append({"materia": "", "anio": "", "calif_final": ""})

    # Asistencia del dorso: días con registro e inasistencias de cada cuatrimestre.
    # Dias con asistencia tomada por cuatrimestre.
    dias = {}
    # Faltas por cuatrimestre.
    inas = {}
    # Para el cuatrimestre 1 y el 2...
    for c in (1, 2):
        # ...cuenta los dias distintos con registro...
        dias[c] = RegistroAsistencia.objects.filter(
            alumno=alumno, fecha__month__in=MESES_CUATRIMESTRE[c],
        ).values("fecha").distinct().count()
        # ...y las faltas del alumno.
        inas[c] = _inasistencias_alumno_cuat(alumno, c)

    # Firmas: quién tomó conocimiento en cada cuatrimestre.
    # Conjunto de pares (cuatrimestre, tipo) que ya estan firmados.
    firmadas = set(ConfirmacionRite.objects.filter(alumno=alumno).values_list("cuatrimestre", "tipo"))
    # Lista para dibujar la tabla de firmas.
    firmas = []
    # Recorre los 3 tipos de firmante.
    for tipo, nombre in ConfirmacionRite.TIPO_CHOICES:
        # Agrega la fila de ese firmante.
        firmas.append({
            "tipo": tipo,
            "nombre": nombre,
            # True si ya firmo el 1° cuatrimestre.
            "c1": (1, tipo) in firmadas,
            # True si ya firmo el 2°.
            "c2": (2, tipo) in firmadas,
            # [(1, firmada?), (2, firmada?)] para dibujar una celda por cuatrimestre.
            "estados": [(c, (c, tipo) in firmadas) for c in (1, 2)],
            # Si el usuario actual puede poner esta firma (para mostrar el boton).
            "puede_firmar": _puede_firmar(request, tipo),
        })

    # Preceptor/a: el que figura en alguna planilla del curso del alumno.
    # Busca el nombre del preceptor en las planillas de las materias del alumno.
    preceptor = (
        PlanillaDatos.objects.filter(materia__in=materias)
        .exclude(preceptor="").values_list("preceptor", flat=True).first()
    )

    # Diccionario con todo lo que usa boletin.html.
    return {
        "alumno": alumno,
        "nombre": f"{alumno.apellido}, {alumno.nombre}",
        "dni": alumno.dni,
        "anio": alumno.anio,
        "division": alumno.division,
        "preceptor": preceptor or "—",
        "filas": filas,
        "intensifican": intensifican,
        "dias": dias,
        # Total de dias de clase del año.
        "dias_total": dias[1] + dias[2],
        # Faltas de cada cuatrimestre con coma.
        "inasistencias": {c: _formato_ar(inas[c]) for c in (1, 2)},
        # Total de faltas del año.
        "total_inasistencias": _formato_ar(inas[1] + inas[2]),
        "firmas": firmas,
        # Para que el template sepa si lo esta mirando el alumno.
        "es_alumno": _rol(request) == "alumno",
        "ciclo_lectivo": timezone.now().year,
    }


# Entra cualquier rol del sistema.
@rol_requerido("alumno", "docente", "administrativo", "directivo")
# VISTA: muestra el boletin.
def alumno_ver_boletin(request):
    """Boletín (RITE) de un alumno. Bloqueado hasta que se publique el año."""
    # Si todavia no esta publicado (y no es gestion)...
    if not _puede_ver_boletin(request):
        # ...avisa...
        messages.warning(request, "El boletín se habilita a fin de año. Mientras tanto podés consultar las notas en el inicio del módulo.")
        # ...y lo manda de vuelta al menu.
        return redirect("calificaciones_menu")

    # Averigua de que alumno hay que mostrar el boletin.
    alumno = _alumno_a_mostrar(request)
    # Si no hay alumno elegido...
    if alumno is None:
        # ...lo manda al buscador.
        return redirect("alumno_seleccionar")
    # Dibuja el boletin con todos los datos.
    return render(request, "calificaciones/boletin.html", _datos_rite(alumno, request))


# Entra cualquier rol.
@rol_requerido("alumno", "docente", "administrativo", "directivo")
# Solo por POST (boton de firmar).
@require_POST
# VISTA: registra una firma del boletin.
def confirmar_rite(request):
    """Registra que alguien tomó conocimiento del boletín (quién y cuándo)."""
    # No se puede firmar un boletin que no esta publicado.
    if not _puede_ver_boletin(request):
        messages.warning(request, "El boletín se habilita a fin de año. Todavía no se pueden registrar firmas.")
        return redirect("calificaciones_menu")

    # Alumno del boletin que se firma.
    alumno = _alumno_a_mostrar(request)
    if alumno is None:
        return redirect("alumno_seleccionar")

    # A donde volver despues: al boletin de ese mismo alumno.
    destino = redirect(f"{reverse('alumno_ver_boletin')}?alumno_id={alumno.id}")
    # Tipo de firma que llego del formulario.
    tipo = request.POST.get("tipo", "").strip()
    # Cuatrimestre que se firma.
    cuat = request.POST.get("cuat", "")
    # Si el tipo o el cuatrimestre no son validos, no hace nada (alguien toco el formulario).
    if tipo not in dict(ConfirmacionRite.TIPO_CHOICES) or cuat not in ("1", "2"):
        return destino

    # Verifica que este usuario pueda poner esa firma.
    if not _puede_firmar(request, tipo):
        # Nombre lindo del tipo de firma para el mensaje.
        nombre = dict(ConfirmacionRite.TIPO_CHOICES)[tipo]
        messages.error(request, f"Tu usuario no puede registrar la firma de {nombre}.")
        return destino

    # Crea la firma o, si ya existia, la actualiza (no se duplica).
    ConfirmacionRite.objects.update_or_create(
        alumno=alumno, cuatrimestre=int(cuat), tipo=tipo,
        # Guarda que usuario firmo.
        defaults={"usuario": request.user.get_username()},
    )
    # Cartel de exito.
    messages.success(request, "Firma registrada.")
    return destino


# ─────────────────────────────────────────────
#  DOCENTE: CARGAR NOTAS (grilla con guardado automático)
# ─────────────────────────────────────────────

# Solo docentes.
@rol_requerido("docente")
# Manda la cookie CSRF que necesita el JavaScript para guardar.
@ensure_csrf_cookie
# VISTA (parte de Lautaro): grilla para cargar notas. cuat y materia_id vienen de la URL.
def profesor_cargar_notas(request, cuat, materia_id):
    """Grilla de notas del cuatrimestre: cada celda se guarda sola al cambiarla."""
    # Trae la materia solo si es de este docente.
    materia = _materia_del_docente(request, materia_id)
    # Si no es suya o el cuatrimestre no es 1 ni 2...
    if materia is None or cuat not in (1, 2):
        # ...error...
        messages.error(request, "No podés cargar notas en esa materia.")
        # ...y vuelve al menu.
        return redirect("calificaciones_menu")

    # Columnas de la grilla.
    categorias = _categorias(materia)
    # Sin categorias no hay donde cargar notas...
    if not categorias:
        messages.warning(request, "Primero creá al menos una categoría de evaluación para esta materia.")
        # ...lo manda a crear categorias.
        return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)

    # Datos para que el JavaScript calcule igual que el servidor.
    # Agrupa las columnas.
    grupos = _grupos_de_categorias(categorias)
    # Por cada grupo...
    for grupo in grupos:
        # ...calcula su peso...
        peso_grupo = grupo["peso"] if grupo["peso"] is not None else Decimal(len(grupo["cats"]))
        # ...y a cada categoria le agrega datos para el JavaScript:
        for cat in grupo["cats"]:
            # una clave del grupo,
            cat["grupo_key"] = grupo["nombre"] or f"_cat{cat['id']}"
            # su peso como texto
            cat["peso_js"] = _num_limpio(cat["peso"] if cat["peso"] is not None else Decimal("1"))
            # y el peso del grupo.
            cat["peso_grupo_js"] = _num_limpio(peso_grupo)

    notas = {}  # {(alumno_id, categoria_id): valor}
    # Trae las notas de la materia en el cuatrimestre...
    for n in NotaEvaluacion.objects.filter(materia=materia, cuatrimestre=cuat).order_by("id"):
        # ...y las guarda con clave (alumno, categoria).
        notas[(n.alumno_id, n.categoria_id)] = n.valor
    # Cierres por alumno.
    cierres = {
        c.alumno_id: c
        for c in CierreCuatrimestre.objects.filter(materia=materia, cuatrimestre=cuat)
    }

    # Una fila por alumno.
    filas = []
    # Recorre los alumnos del curso.
    for alumno in _alumnos_del_curso(materia.curso):
        # Notas de este alumno: {categoria: valor}.
        notas_alumno = {
            cat["id"]: notas[(alumno.id, cat["id"])]
            for cat in categorias if (alumno.id, cat["id"]) in notas
        }
        # Resumen del cuatrimestre del alumno.
        datos = _datos_cuatrimestre(notas_alumno, categorias, cierres.get(alumno.id))
        # Nota como numero.
        calif = Decimal(datos["calificacion"]) if datos["calificacion"] else None

        # Asistencia anual en la materia.
        asistencia = _asistencia_materia(alumno.id, materia)
        # OK si no hay registros o llega al 80 %.
        asistencia_ok = asistencia is None or asistencia["suficiente"]

        # Inasistencias: se leen del módulo Asistencia (no se cargan acá).
        # Faltas del alumno en esta materia y cuatrimestre (ausente = 1, tardanza = 0,5). Ya no hay carga manual.
        inas = _inasistencias_materia_cuat(alumno.id, materia, cuat)

        # Fila del alumno para la grilla.
        filas.append({
            "id": alumno.id,
            "nombre": f"{alumno.apellido}, {alumno.nombre}",
            # Una celda por categoria con su nota (con coma).
            "celdas": [
                {
                    "cat": cat,
                    "valor": _formato_ar(notas_alumno.get(cat["id"])) or "",
                }
                for cat in categorias
            ],
            "valoracion": datos["valoracion"],
            "calificacion": datos["calificacion"],
            "estado": _estado_materia(calif, asistencia_ok),
            "aprobada": datos["aprobada"] and asistencia_ok,
            "asistencia_ok": asistencia_ok,
            "asistencia_pct": _formato_ar(asistencia["porcentaje"]) if asistencia else "",
            "inasistencias": _formato_ar(inas) or "",
        })

    # Dibuja la grilla.
    return render(request, "calificaciones/cargar_notas.html", {
        "cuat": cuat,
        "materia": materia,
        "curso": _texto_curso(materia.curso),
        "fecha_cierre": _fecha_cierre(materia, cuat),  # si está cerrado, la grilla es de solo lectura
        "excel_disponible": EXCEL_DISPONIBLE,
        "filas": filas,
        "categorias": categorias,
        "grupos": grupos,
        # True si alguna columna tiene grupo (para dibujar la fila de titulos de grupo).
        "tiene_grupos": any(g["nombre"] for g in grupos),
        # True si se usan pesos.
        "con_pesos": any(c["peso"] is not None for c in categorias),
    })


# Controles que comparten los 2 guardados automaticos (nota y valoracion).
def _validar_ajax(request, cuat, materia_id):
    """Chequeos comunes de los guardados automáticos.

    Devuelve (materia, alumno, None) si todo está bien, o (None, None, respuesta
    de error) si algo falla.
    """
    # Solo se acepta POST (405 = metodo no permitido).
    if request.method != "POST":
        return None, None, JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    # Cuatrimestre valido (400 = pedido incorrecto).
    if cuat not in (1, 2):
        return None, None, JsonResponse({"ok": False, "error": "Cuatrimestre inválido"}, status=400)
    # La materia tiene que ser del docente...
    materia = _materia_del_docente(request, materia_id)
    if materia is None:
        # ...si no, 403 = prohibido.
        return None, None, JsonResponse({"ok": False, "error": "Esa materia no es tuya"}, status=403)
    # Si el cuatrimestre esta cerrado...
    if _fecha_cierre(materia, cuat):
        # ...no deja guardar (409 = conflicto).
        return None, None, JsonResponse({"ok": False, "error": _aviso_cerrado(cuat)}, status=409)
    # El alumno tiene que ser del curso de la materia...
    alumno = _alumno_de_la_materia(materia, request.POST.get("alumno_id") or 0)
    if alumno is None:
        # ...si no, 404 = no encontrado.
        return None, None, JsonResponse({"ok": False, "error": "Alumno no encontrado"}, status=404)
    # Todo bien: devuelve materia y alumno, sin error.
    return materia, alumno, None


# Solo docentes.
@rol_requerido("docente")
# VISTA AJAX: guarda una celda de nota. La llama el JavaScript y responde con JSON.
def profesor_guardar_nota(request, cuat, materia_id):
    """Guardado automático de una celda de nota. Celda vacía = borrar la nota."""
    # Hace los controles comunes.
    materia, alumno, error = _validar_ajax(request, cuat, materia_id)
    # Si alguno fallo, devuelve ese error.
    if error:
        return error

    # Busca la categoria y verifica que sea de esta materia.
    categoria = CategoriaEvaluacion.objects.filter(
        id=request.POST.get("cat_id") or 0, materia=materia,
    ).first()
    # Si no existe, error 404.
    if categoria is None:
        return JsonResponse({"ok": False, "error": "Categoría no encontrada"}, status=404)

    # Lo que escribio el docente en la celda.
    texto = request.POST.get("valor", "").strip()
    # Datos que identifican la nota (alumno, materia, categoria, cuatrimestre).
    filtro = {"alumno": alumno, "materia": materia, "categoria": categoria, "cuatrimestre": cuat}
    # Celda vacia...
    if texto == "":
        # ...borra la nota. (**filtro pasa el diccionario como parametros).
        NotaEvaluacion.objects.filter(**filtro).delete()
    # Si escribio algo...
    else:
        # ...lo convierte a nota de 0 a 10...
        valor = _nota_desde_texto(texto)
        # ...y si no es valida...
        if valor is None:
            # ...devuelve error 400 con el motivo.
            return JsonResponse({"ok": False, "error": f"'{texto}' no es una nota válida (0 a 10)"}, status=400)
        # Si por algún motivo hubiera notas repetidas en la celda, quedan en una sola.
        # Borra la nota anterior...
        NotaEvaluacion.objects.filter(**filtro).delete()
        # ...y crea la nueva.
        NotaEvaluacion.objects.create(valor=valor, **filtro)

    # Devuelve la calificación recalculada para refrescar la fila.
    # Vuelve a leer las notas del alumno...
    notas = {
        n.categoria_id: n.valor
        for n in NotaEvaluacion.objects.filter(alumno=alumno, materia=materia, cuatrimestre=cuat)
    }
    # ...recalcula la nota del cuatrimestre...
    calif = _calificacion_entera(notas, _categorias(materia))
    # ...y la asistencia...
    asistencia = _asistencia_materia(alumno.id, materia)
    asistencia_ok = asistencia is None or asistencia["suficiente"]
    # ...y le responde al JavaScript para que actualice la fila.
    return JsonResponse({
        "ok": True,
        "calificacion": str(calif) if calif is not None else "",
        "estado_materia": _estado_materia(calif, asistencia_ok),
    })


# Solo docentes.
@rol_requerido("docente")
# VISTA AJAX: guarda la valoracion TEA/TEP/TED.
def profesor_guardar_valoracion(request, cuat, materia_id):
    """Guardado automático de la valoración preliminar (TEA / TEP / TED)."""
    # Controles comunes.
    materia, alumno, error = _validar_ajax(request, cuat, materia_id)
    if error:
        return error

    # Valoracion recibida, en mayusculas.
    valoracion = request.POST.get("valoracion", "").strip().upper()
    # Solo acepta TEA, TEP, TED o vacio.
    if valoracion not in ("TEA", "TEP", "TED", ""):
        return JsonResponse({"ok": False, "error": "Valoración inválida"}, status=400)

    # Crea o actualiza el cierre del alumno con esa valoracion.
    CierreCuatrimestre.objects.update_or_create(
        alumno=alumno, materia=materia, cuatrimestre=cuat,
        defaults={"valoracion_preliminar": valoracion},
    )
    # Responde OK.
    return JsonResponse({"ok": True, "valoracion": valoracion})


# ─────────────────────────────────────────────
#  DOCENTE: CATEGORÍAS DE EVALUACIÓN
# ─────────────────────────────────────────────

# Valida el peso (%) de una categoria.
def _peso_desde_texto(texto):
    """Peso % de una categoría (mayor a 0 y hasta 100), o None si está vacío.

    Lanza ValueError con el motivo si el texto no sirve.
    """
    # Vacio = sin peso.
    if not (texto or "").strip():
        return None
    # Lo convierte a numero.
    peso = _decimal_desde_texto(texto)
    # Si no es un numero...
    if peso is None:
        # ...lanza un error con el motivo (raise).
        raise ValueError("no es un número")
    # Tiene que ser mayor a 0 y hasta 100.
    if peso <= 0 or peso > 100:
        raise ValueError("tiene que estar entre 0 y 100")
    return peso


# Lee y valida el formulario de categoria.
def _datos_categoria(request):
    """Lee nombre, grupo y peso del formulario. Devuelve (datos, error)."""
    # Nombre sin espacios sobrantes.
    nombre = request.POST.get("nombre", "").strip()
    # El nombre es obligatorio.
    if not nombre:
        return None, "El nombre no puede estar vacío."
    # Intenta leer el peso...
    try:
        peso = _peso_desde_texto(request.POST.get("peso", ""))
    # ...y si es invalido devuelve el mensaje de error.
    except ValueError as motivo:
        return None, f"El peso '{request.POST.get('peso')}' {motivo}."
    # Devuelve los datos listos y None como error.
    return {"nombre": nombre, "grupo": request.POST.get("grupo", "").strip(), "peso": peso}, None


# Solo docentes.
@rol_requerido("docente")
# VISTA: lista las categorias de la materia.
def profesor_categorias(request, cuat, materia_id):
    """Lista de categorías con el formulario para agregar o editar."""
    # La materia tiene que ser del docente.
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    # Categorias actuales.
    categorias = _categorias(materia)
    # Si la URL trae ?editar=ID, se esta editando esa categoria.
    edit_id = request.GET.get("editar")
    # Busca esa categoria en la lista (None si no esta).
    editando = next((c for c in categorias if str(c["id"]) == edit_id), None)
    # Dibuja la pantalla.
    return render(request, "calificaciones/gestionar_categorias.html", {
        # True si algun cuatrimestre esta cerrado (para avisar).
        "hay_cerrados": any(_fecha_cierre(materia, c) for c in (1, 2)),
        "cuat": cuat,
        "materia": materia,
        "curso": _texto_curso(materia.curso),
        "categorias": categorias,
        "editando": editando,
    })


# Solo docentes.
@rol_requerido("docente")
# Solo POST.
@require_POST
# VISTA: crea una categoria.
def profesor_agregar_categoria(request, cuat, materia_id):
    """Crea una categoría nueva al final de la grilla."""
    # Verifica que la materia sea suya.
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    # Lee el formulario.
    datos, error = _datos_categoria(request)
    # Si hay error lo muestra.
    if error:
        messages.error(request, error)
    # Si esta todo bien...
    else:
        # ...busca la categoria con el orden mas alto...
        ultimo = CategoriaEvaluacion.objects.filter(materia=materia).order_by("-orden").first()
        # ...la nueva va una posicion despues...
        orden = (ultimo.orden if ultimo else 0) + 1
        # ...la crea...
        CategoriaEvaluacion.objects.create(materia=materia, orden=orden, **datos)
        # ...y avisa.
        messages.success(request, f"Categoría '{datos['nombre']}' creada.")
    # Vuelve a la lista de categorias.
    return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)


# Solo docentes.
@rol_requerido("docente")
# Solo POST.
@require_POST
# VISTA: edita una categoria (cat_id viene de la URL).
def profesor_editar_categoria(request, cuat, materia_id, cat_id):
    """Cambia nombre, grupo y peso de una categoría."""
    # Verifica que la materia sea suya.
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    # Busca la categoria de esa materia; si no existe muestra la pagina 404.
    categoria = get_object_or_404(CategoriaEvaluacion, id=cat_id, materia=materia)
    # Lee y valida el formulario.
    datos, error = _datos_categoria(request)
    # Si hay error lo muestra.
    if error:
        messages.error(request, error)
    # Si esta todo bien...
    else:
        # ...recorre los datos (nombre, grupo, peso)...
        for campo, valor in datos.items():
            # ...y los copia a la categoria (setattr = categoria.campo = valor).
            setattr(categoria, campo, valor)
        # Guarda en la base.
        categoria.save()
        messages.success(request, "Categoría actualizada.")
    # Vuelve a la lista.
    return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)


# Solo docentes.
@rol_requerido("docente")
# Solo POST (no se puede borrar entrando a un link).
@require_POST
# VISTA: borra una categoria.
def profesor_eliminar_categoria(request, cuat, materia_id, cat_id):
    """Borra una categoría y sus notas (solo por POST, con confirmación)."""
    # Verifica que la materia sea suya.
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    # Busca la categoria o da 404.
    categoria = get_object_or_404(CategoriaEvaluacion, id=cat_id, materia=materia)

    # Si la categoría tiene notas de un cuatrimestre cerrado, borrarla cambiaría
    # notas que ya quedaron fijas: no se permite.
    # Lista de cuatrimestres cerrados de la materia.
    cerrados = [c for c in (1, 2) if _fecha_cierre(materia, c)]
    # Si la categoria tiene notas en un cuatrimestre cerrado...
    if NotaEvaluacion.objects.filter(categoria=categoria, cuatrimestre__in=cerrados).exists():
        # ...no deja borrarla...
        messages.error(request, f"No se puede eliminar '{categoria.nombre}': tiene notas de un cuatrimestre cerrado.")
        # ...y vuelve a la lista.
        return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)

    # Borra la categoria (y por CASCADE, todas sus notas).
    categoria.delete()
    messages.success(request, f"Categoría '{categoria.nombre}' eliminada.")
    # Vuelve a la lista.
    return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)


# ─────────────────────────────────────────────
#  DOCENTE: IMPORTAR NOTAS DESDE EXCEL
# ─────────────────────────────────────────────

# Nombre con el que se guarda el Excel leido en la sesion del usuario.
def _clave_excel(cuat, materia):
    """Clave de sesión donde se guarda el Excel leído hasta que se confirma."""
    return f"excel_{cuat}_{materia.id}"


# Busca un alumno del curso por el texto de la primera columna del Excel.
def _buscar_alumno_por_nombre(materia, texto):
    """Alumno del curso por 'Apellido, Nombre', o por apellido/nombre solo."""
    # Alumnos del curso.
    alumnos = _alumnos_del_curso(materia.curso)
    # Si el texto viene como "Apellido, Nombre"...
    if ", " in texto:
        # ...lo parte en apellido y nombre...
        apellido, _, nombre = texto.partition(", ")
        # ...y busca sin importar mayusculas (iexact).
        alumno = alumnos.filter(apellido__iexact=apellido.strip(), nombre__iexact=nombre.strip()).first()
        # Si lo encontro, lo devuelve.
        if alumno:
            return alumno
    # Si no, prueba que coincida solo el nombre o solo el apellido.
    return alumnos.filter(Q(nombre__iexact=texto) | Q(apellido__iexact=texto)).first()


# Solo docentes.
@rol_requerido("docente")
# VISTA: subir el Excel y mostrar la vista previa (todavia no guarda nada).
def profesor_cargar_excel(request, cuat, materia_id):
    """Paso 1: subir el Excel y mostrar la vista previa."""
    # Verifica que la materia sea suya.
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    # Si el cuatrimestre esta cerrado no se puede importar.
    if _fecha_cierre(materia, cuat):
        messages.error(request, _aviso_cerrado(cuat))
        return redirect("profesor_cargar_notas", cuat=cuat, materia_id=materia.id)

    # Datos basicos de la pantalla.
    contexto = {
        "cuat": cuat,
        "materia": materia,
        "curso": _texto_curso(materia.curso),
        "excel_disponible": EXCEL_DISPONIBLE,
    }
    # Si entro por GET (solo abrio la pagina)...
    if request.method != "POST":
        # ...muestra el formulario para elegir el archivo.
        return render(request, "calificaciones/cargar_excel.html", contexto)

    # Archivo subido (request.FILES).
    archivo = request.FILES.get("archivo")
    # Si no eligio archivo, error.
    if archivo is None:
        messages.error(request, "Elegí un archivo Excel para subir.")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    # Intenta cargar la libreria de Excel...
    try:
        import openpyxl
    # ...y si no esta instalada, avisa.
    except ImportError:
        messages.error(request, "Falta instalar la librería openpyxl (pip install openpyxl).")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    # Abre el Excel y toma la hoja activa...
    try:
        hoja = openpyxl.load_workbook(archivo, read_only=True, data_only=True).active
        # ...y lee todas las filas como listas de valores.
        filas_excel = list(hoja.iter_rows(values_only=True))
    # Si el archivo no es un Excel valido...
    except Exception:
        # ...muestra un error en vez de romperse.
        messages.error(request, "No se pudo leer el archivo. Tiene que ser un Excel (.xlsx).")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    # Si no tiene filas, error.
    if not filas_excel:
        messages.error(request, "El archivo está vacío.")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    # Primera fila = titulos de las columnas, limpios.
    encabezados = [str(h).strip() if h is not None else "" for h in filas_excel[0]]
    # Categorias de la materia por nombre: {nombre: categoria}.
    categorias = {c["nombre"]: c for c in _categorias(materia)}
    # Columnas del Excel que coinciden con una categoría: {índice: categoría}.
    # Se queda con las columnas cuyo titulo coincide con una categoria (la columna 0 es el alumno).
    columnas = {i: categorias[h] for i, h in enumerate(encabezados) if i > 0 and h in categorias}

    # Lo que se muestra en pantalla.
    vista_previa = []
    # Lo que se va a guardar si confirma.
    para_guardar = []
    # Recorre las filas de datos (saltea la de titulos).
    for fila in filas_excel[1:]:
        # Saltea filas vacias.
        if not fila or not fila[0]:
            continue
        # Nombre del alumno (primera columna).
        nombre = str(fila[0]).strip()
        # Lo busca en el curso.
        alumno = _buscar_alumno_por_nombre(materia, nombre)
        # Notas de esa fila: {id de categoria: texto}.
        notas = {}
        # Por cada columna reconocida...
        for i, cat in columnas.items():
            # ...toma el valor de la celda...
            valor = fila[i] if i < len(fila) else None
            # ...y lo guarda como texto.
            notas[cat["id"]] = "" if valor is None else str(valor).strip()
        # Fila de la vista previa.
        vista_previa.append({
            "nombre": nombre,
            # Si el alumno existe en el curso.
            "encontrado": alumno is not None,
            # Valores a mostrar (raya si esta vacio).
            "valores": [notas.get(cat["id"]) or "—" for cat in columnas.values()],
        })
        # Solo se guardan los alumnos encontrados.
        if alumno is not None:
            para_guardar.append({"alumno_id": alumno.id, "notas": {str(k): v for k, v in notas.items()}})

    # Guarda los datos en la sesion hasta que el docente confirme.
    request.session[_clave_excel(cuat, materia)] = para_guardar
    # Agrega al contexto lo de la vista previa.
    contexto.update({
        "columnas": [cat["nombre"] for cat in columnas.values()],
        "vista_previa": vista_previa,
        "hay_para_guardar": bool(para_guardar),
    })
    # Muestra la pantalla de confirmacion.
    return render(request, "calificaciones/confirmar_excel.html", contexto)


# Solo docentes.
@rol_requerido("docente")
# Solo POST.
@require_POST
# VISTA: guarda de verdad las notas del Excel.
def profesor_confirmar_excel(request, cuat, materia_id):
    """Paso 2: guardar las notas de la vista previa confirmada."""
    # Verifica que la materia sea suya.
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    # No se guarda en un cuatrimestre cerrado.
    if _fecha_cierre(materia, cuat):
        messages.error(request, _aviso_cerrado(cuat))
        return redirect("profesor_cargar_notas", cuat=cuat, materia_id=materia.id)

    # Saca los datos de la sesion (pop los lee y los borra).
    filas = request.session.pop(_clave_excel(cuat, materia), None)
    # Si no hay datos (se vencio la sesion o entro directo), error.
    if not filas:
        messages.error(request, "No se encontraron datos del Excel. Volvé a subir el archivo.")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    # Categorias validas de la materia.
    categorias = {str(c["id"]): c["id"] for c in _categorias(materia)}
    # Contador de notas guardadas.
    guardadas = 0
    # Contador de valores invalidos.
    omitidas = 0
    # Recorre cada alumno del Excel.
    for fila in filas:
        # Vuelve a verificar que el alumno sea del curso.
        alumno = _alumno_de_la_materia(materia, fila["alumno_id"])
        if alumno is None:
            continue
        # Recorre sus notas.
        for cat_id, texto in fila["notas"].items():
            # Saltea categorias que ya no existen y celdas vacias.
            if cat_id not in categorias or texto == "":
                continue
            # Valida que sea una nota de 0 a 10.
            valor = _nota_desde_texto(texto)
            # Si no lo es...
            if valor is None:
                # ...la cuenta como omitida y sigue.
                omitidas += 1
                continue
            # Datos que identifican la nota.
            filtro = {"alumno": alumno, "materia": materia,
                      "categoria_id": categorias[cat_id], "cuatrimestre": cuat}
            # Borra la nota anterior...
            NotaEvaluacion.objects.filter(**filtro).delete()
            # ...crea la nueva...
            NotaEvaluacion.objects.create(valor=valor, **filtro)
            # ...y suma uno al contador.
            guardadas += 1

    # Cartel con el resultado.
    messages.success(request, f"Se cargaron {guardadas} notas desde Excel.")
    # Avisa si hubo valores descartados.
    if omitidas:
        messages.warning(request, f"Se omitieron {omitidas} valores que no eran notas de 0 a 10.")
    # Vuelve a la grilla de notas.
    return redirect("profesor_cargar_notas", cuat=cuat, materia_id=materia.id)


# Solo docentes.
@rol_requerido("docente")
# VISTA: genera y descarga un Excel modelo.
def profesor_descargar_plantilla(request, cuat, materia_id):
    """Descarga un Excel con los alumnos y una columna por categoría."""
    # Verifica que la materia sea suya.
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    # Carga la libreria de Excel y sus herramientas de estilo...
    try:
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    # ...y avisa si no esta instalada.
    except ImportError:
        messages.error(request, "Falta instalar la librería openpyxl (pip install openpyxl).")
        return redirect("profesor_cargar_notas", cuat=cuat, materia_id=materia.id)

    # Columnas de la materia.
    categorias = _categorias(materia)
    # Crea un Excel nuevo en memoria.
    libro = openpyxl.Workbook()
    # Toma su hoja.
    hoja = libro.active
    # Le pone nombre a la hoja.
    hoja.title = f"{cuat}° cuatrimestre"

    # Borde fino en los 4 lados de la celda.
    borde = Border(*(Side(style="thin"),) * 4)
    # Titulos: "Alumno" y despues una columna por categoria.
    encabezado = ["Alumno"] + [c["nombre"] for c in categorias]
    # Por cada titulo (col empieza en 1)...
    for col, texto in enumerate(encabezado, start=1):
        # ...escribe la celda en la fila 1...
        celda = hoja.cell(row=1, column=col, value=texto)
        # ...letra blanca en negrita...
        celda.font = Font(bold=True, color="FFFFFF")
        # ...fondo azul...
        celda.fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        # ...centrada...
        celda.alignment = Alignment(horizontal="center")
        # ...con borde...
        celda.border = borde
        # ...y define el ancho de la columna.
        hoja.column_dimensions[get_column_letter(col)].width = 30 if col == 1 else 18

    # Una fila por alumno, desde la fila 2.
    for fila, alumno in enumerate(_alumnos_del_curso(materia.curso), start=2):
        # Escribe "Apellido, Nombre" en la primera columna.
        hoja.cell(row=fila, column=1, value=f"{alumno.apellido}, {alumno.nombre}")
        # A todas las celdas de la fila...
        for col in range(1, len(encabezado) + 1):
            # ...les pone borde.
            hoja.cell(row=fila, column=col).border = borde

    # Respuesta HTTP con tipo "archivo de Excel".
    respuesta = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    # Nombre del archivo.
    nombre_archivo = f"plantilla_{materia.nombre}_{_texto_curso(materia.curso)}_{cuat}cuat.xlsx"
    # Content-Disposition attachment hace que el navegador lo descargue.
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo.replace(" ", "_")}"'
    # Escribe el Excel dentro de la respuesta.
    libro.save(respuesta)
    # Lo envia.
    return respuesta


# ─────────────────────────────────────────────
#  PLANILLA DE CALIFICACIONES (hoja oficial imprimible)
# ─────────────────────────────────────────────

# Entran docentes, secretaria y directivo.
@rol_requerido("docente", "administrativo", "directivo")
# VISTA (parte de Axel): planilla oficial de la materia.
def profesor_planilla(request, cuat, materia_id):
    """Planilla oficial de la materia, con los dos cuatrimestres.

    El docente de la materia la completa y la guarda; secretaría y directivo
    la ven en modo lectura para imprimirla.
    """
    # Materia que el usuario puede VER (docente dueño o gestion).
    materia = _materia_para_consulta(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "No podés consultar esa materia.")
        return redirect("calificaciones_menu")

    # Solo puede editar el docente de la materia; gestion la ve en solo lectura.
    puede_editar = _materia_del_docente(request, materia.id) is not None

    # Si se envio el formulario...
    if request.method == "POST":
        # ...y no puede editar...
        if not puede_editar:
            # ...error...
            messages.error(request, "Solo el docente de la materia puede guardar los cambios.")
            # ...y vuelve a la planilla.
            return redirect("profesor_planilla", cuat=cuat, materia_id=materia.id)
        # Guarda los cambios (y cierra o reabre si corresponde).
        _guardar_planilla(request, materia, cuat)
        # Vuelve a mostrar la planilla (POST -> redirect).
        return redirect("profesor_planilla", cuat=cuat, materia_id=materia.id)

    # Columnas de la materia.
    categorias = _categorias(materia)
    # Una fila por alumno con todos sus datos.
    filas = _filas_planilla(materia, categorias, cuat)
    # Turno y preceptor guardados (si hay).
    datos_planilla = PlanillaDatos.objects.filter(materia=materia).first()

    # La hoja mide 200 mm: lo que dejan las columnas fijas se reparte entre
    # las columnas de notas parciales (una por categoría, en cada cuatrimestre).
    # Ancho en mm de cada columna de parciales, con un minimo de 5.
    ancho_parcial = max(5.0, (200 - 143.6) / (2 * max(len(categorias), 1)))

    # Dibuja la planilla.
    return render(request, "calificaciones/planilla.html", {
        "cuat": cuat,
        "materia": materia,
        "curso": _texto_curso(materia.curso),
        "docente_nombre": _nombre_docente(materia),
        "turno": datos_planilla.turno if datos_planilla else "",
        "preceptor": datos_planilla.preceptor if datos_planilla else "",
        "puede_editar": puede_editar,
        "fecha_cierre": _fecha_cierre(materia, cuat),  # None = cuatrimestre abierto
        "filas": filas,
        "categorias": categorias,
        "ancho_parcial": f"{ancho_parcial:.1f}",
        # Columnas de cada cuatrimestre: parciales (mínimo 1) + las fijas.
        # Cantidad de columnas del bloque del 1° cuatrimestre (para el colspan).
        "col_1c": max(len(categorias), 1) + 3,
        # Cantidad de columnas del bloque del 2° cuatrimestre.
        "col_2c": max(len(categorias), 1) + 4,
        # Numeros de los renglones vacios hasta completar 37.
        "numeros_vacios": range(len(filas) + 1, 38),  # la hoja oficial tiene 37 renglones
        # Clases dadas en cada cuatrimestre.
        "clases": {1: _clases_dadas(materia, 1), 2: _clases_dadas(materia, 2)},
        # Cuadro de totales del pie.
        "totales": _totales_planilla(filas),
        "ciclo_lectivo": timezone.now().year,
    })


# Arma una fila por alumno para la planilla.
def _filas_planilla(materia, categorias, cuat):
    """Una fila por alumno con todo lo que muestra la planilla."""
    notas = {1: {}, 2: {}}  # {cuat: {alumno_id: {categoria_id: valor}}}
    # Recorre todas las notas de la materia...
    for n in NotaEvaluacion.objects.filter(materia=materia).order_by("id"):
        # ...si el cuatrimestre es 1 o 2...
        if n.cuatrimestre in notas:
            # ...las agrupa por cuatrimestre, alumno y categoria.
            notas[n.cuatrimestre].setdefault(n.alumno_id, {})[n.categoria_id] = n.valor
    # Cierres con clave (alumno, cuatrimestre).
    cierres = {
        (c.alumno_id, c.cuatrimestre): c
        for c in CierreCuatrimestre.objects.filter(materia=materia)
    }

    # Lista de filas.
    filas = []
    # Recorre los alumnos numerandolos desde 1.
    for nro, alumno in enumerate(_alumnos_del_curso(materia.curso), start=1):
        # Cierre del 1° cuatrimestre.
        cierre1 = cierres.get((alumno.id, 1))
        # Cierre del 2°.
        cierre2 = cierres.get((alumno.id, 2))
        # Resumen del 1° cuatrimestre.
        d1 = _datos_cuatrimestre(notas[1].get(alumno.id, {}), categorias, cierre1)
        # Resumen del 2°.
        d2 = _datos_cuatrimestre(notas[2].get(alumno.id, {}), categorias, cierre2)

        # Regla del 80 %: sin asistencia suficiente, nada queda aprobado.
        # Asistencia anual.
        asistencia = _asistencia_materia(alumno.id, materia)
        # OK si no hay registros o llega al 80 %.
        asistencia_ok = asistencia is None or asistencia["suficiente"]
        # Si no alcanza...
        if not asistencia_ok:
            # ...ningun cuatrimestre cuenta como aprobado.
            d1["aprobada"] = d2["aprobada"] = False

        # Inasistencias: se leen del módulo Asistencia (no se cargan acá).
        inas = {
            # Diccionario {1: faltas del 1° cuat., 2: faltas del 2° cuat.}, ya con coma. Solo lectura.
            c: _formato_ar(_inasistencias_materia_cuat(alumno.id, materia, c)) or ""
            for c in (1, 2)
        }

        cierre_actual = cierres.get((alumno.id, cuat))  # el cuatrimestre que se edita
        # Nota final (manual o automatica).
        final = _calificacion_final(d1, d2, cierre1, cierre2)

        # Fila del alumno.
        filas.append({
            "nro": nro,
            "id": alumno.id,
            "nombre": f"{alumno.apellido}, {alumno.nombre}",
            # Nombre como va en la planilla impresa: APELLIDO Nombre.
            "nombre_planilla": f"{alumno.apellido.upper()} {alumno.nombre}",
            # C o R.
            "cursada": cierre_actual.cursada if cierre_actual else "C",
            # Datos del 1° cuatrimestre.
            "d1": d1,
            # Datos del 2°.
            "d2": d2,
            "inas1": inas[1],
            "inas2": inas[2],
            # Nota de intensificacion del 1° cuatrimestre.
            "intensificacion": _intensificacion(cierre1),
            # Nota de diciembre.
            "dic": _num_limpio(cierre_actual.nota_diciembre) if cierre_actual and cierre_actual.nota_diciembre is not None else "",
            # Nota de febrero.
            "feb": _num_limpio(cierre_actual.nota_febrero) if cierre_actual and cierre_actual.nota_febrero is not None else "",
            "final": final,
            "final_auto": _final_automatico(d1, d2, cierre1),  # para no guardar lo que ya es automático
            # Final aprobada: tiene final, es 7 o mas y tiene asistencia.
            "final_aprobada": bool(final) and Decimal(final) >= NOTA_APROBACION and asistencia_ok,
            "no_acredita": not asistencia_ok,
        })
    return filas


# Arma el cuadro de totales del pie de la planilla.
def _totales_planilla(filas):
    """Cuadro de totales del pie: 1°C, 2°C, total anual, diciembre y febrero."""
    # Funcion interna: cuenta cuantas filas cumplen una condicion.
    def contar(condicion):
        return sum(1 for f in filas if condicion(f))

    # Funcion interna: dice si una nota aprueba (7 o mas y con asistencia).
    def aprueba(nota_texto, fila):
        return Decimal(nota_texto) >= NOTA_APROBACION and not fila["no_acredita"]

    # Alumnos con nota en diciembre.
    con_dic = [f for f in filas if f["dic"]]
    # Alumnos con nota en febrero.
    con_feb = [f for f in filas if f["feb"]]
    # Cada lista tiene 5 numeros: 1°C, 2°C, anual, diciembre, febrero.
    return {
        # Cantidad de estudiantes en cada columna.
        "estudiantes": [len(filas), len(filas), len(filas), len(con_dic), len(con_feb)],
        # Aprobados (lambda = funcion cortita de una linea).
        "aprobados": [
            contar(lambda f: f["d1"]["aprobada"]),
            contar(lambda f: f["d2"]["aprobada"]),
            contar(lambda f: f["final_aprobada"]),
            sum(1 for f in con_dic if aprueba(f["dic"], f)),
            sum(1 for f in con_feb if aprueba(f["feb"], f)),
        ],
        # Desaprobados: tienen nota pero no aprueban.
        "desaprobados": [
            contar(lambda f: f["d1"]["tiene_calificacion"] and not f["d1"]["aprobada"]),
            contar(lambda f: f["d2"]["tiene_calificacion"] and not f["d2"]["aprobada"]),
            contar(lambda f: f["final"] and not f["final_aprobada"]),
            sum(1 for f in con_dic if not aprueba(f["dic"], f)),
            sum(1 for f in con_feb if not aprueba(f["feb"], f)),
        ],
        # Sin evaluar: no tienen nota.
        "sin_evaluar": [
            contar(lambda f: not f["d1"]["tiene_calificacion"]),
            contar(lambda f: not f["d2"]["tiene_calificacion"]),
            contar(lambda f: not f["final"]),
            0,
            0,
        ],
    }


# Guarda lo que el docente edito en la planilla.
def _guardar_planilla(request, materia, cuat):
    """Guarda lo editable de la planilla. Según el botón, además cierra o
    reabre el cuatrimestre."""
    # Que boton apreto: guardar, cerrar o reabrir.
    accion = request.POST.get("accion", "guardar")

    # Si apreto "Reabrir"...
    if accion == "reabrir":
        # Reabrir libera las notas: la calificación vuelve a calcularse sola.
        # ...destraba todos los cierres de ese cuatrimestre y borra la nota fija y la fecha.
        CierreCuatrimestre.objects.filter(materia=materia, cuatrimestre=cuat, cerrado=True).update(
            cerrado=False, calificacion=None, fecha_cierre=None,
        )
        # Avisa.
        messages.success(request, f"El {cuat}° cuatrimestre se reabrió: ya se pueden cambiar las notas.")
        # Y termina aca (no guarda nada mas).
        return

    # True si apreto "Cerrar" y todavia no estaba cerrado.
    cerrar = accion == "cerrar" and not _fecha_cierre(materia, cuat)

    # Encabezado: turno y preceptor/a.
    # Guarda turno y preceptor (recortados al largo maximo).
    PlanillaDatos.objects.update_or_create(materia=materia, defaults={
        "turno": request.POST.get("turno", "").strip()[:50],
        "preceptor": request.POST.get("preceptor", "").strip()[:100],
    })

    # Columnas.
    categorias = _categorias(materia)
    # Filas actuales por id de alumno.
    filas = {f["id"]: f for f in _filas_planilla(materia, categorias, cuat)}
    # Avisos para mostrar al final.
    avisos = []
    # Fecha y hora del cierre.
    ahora = timezone.now()

    # Recorre cada alumno.
    for alumno in _alumnos_del_curso(materia.curso):
        # Su fila actual.
        fila = filas[alumno.id]
        # Trae (o crea) el cierre del alumno en los 2 cuatrimestres.
        cierres = {
            c: CierreCuatrimestre.objects.get_or_create(alumno=alumno, materia=materia, cuatrimestre=c)[0]
            for c in (1, 2)
        }
        cierre = cierres[cuat]  # el cuatrimestre que se está mirando

        # Cursa/recursa, diciembre y febrero van en el cuatrimestre que se mira.
        # Cursada que eligio el docente para este alumno.
        cursada = request.POST.get(f"cursada_{alumno.id}", "C").strip().upper()
        # Solo acepta C o R.
        cierre.cursada = cursada if cursada in ("C", "R") else "C"
        # Nota de diciembre (None si esta vacia o es invalida).
        cierre.nota_diciembre = _nota_desde_texto(request.POST.get(f"dic_{alumno.id}"))
        # Nota de febrero.
        cierre.nota_febrero = _nota_desde_texto(request.POST.get(f"feb_{alumno.id}"))

        # Intensificación del 1° cuatrimestre: solo si no lo había aprobado y
        # al intensificar llegó a 7 o más.
        # Texto del campo de intensificacion de este alumno.
        texto = request.POST.get(f"intens_{alumno.id}")
        # Si el campo vino en el formulario...
        if texto is not None:
            # ...lo convierte a nota.
            nota = _nota_desde_texto(texto)
            # Nota del 1° cuatrimestre.
            calif1 = fila["d1"]["calificacion"]
            # Si lo dejo vacio...
            if texto.strip() == "":
                # ...saca la intensificacion...
                cierres[1].intensificacion = False
                # ...y su nota.
                cierres[1].calificacion_final = None
            # Si no es una nota de 7 o mas...
            elif nota is None or nota < NOTA_APROBACION:
                # ...agrega un aviso.
                avisos.append(f"{fila['nombre']}: la intensificación tiene que ser una nota de 7 a 10.")
            # Si ya habia aprobado el 1° cuatrimestre...
            elif calif1 and Decimal(calif1) >= NOTA_APROBACION:
                # ...no corresponde intensificar.
                avisos.append(f"{fila['nombre']}: aprobó el 1° cuatrimestre, no necesita intensificación.")
            # Caso valido:
            else:
                # marca la intensificacion...
                cierres[1].intensificacion = True
                # ...y guarda la nota.
                cierres[1].calificacion_final = nota

        # Nota final: se guarda solo si el docente la cambió (si coincide con
        # la automática o queda vacía, se sigue calculando sola).
        # Texto del campo de nota final.
        texto = request.POST.get(f"final_{alumno.id}")
        # Si vino en el formulario...
        if texto is not None:
            # ...lo convierte a nota.
            nota = _nota_desde_texto(texto)
            # Nota final que saldria automaticamente.
            automatica = _final_automatico(fila["d1"], fila["d2"], cierres[1])
            # Vacio: vuelve a la automatica.
            if texto.strip() == "":
                cierres[2].calificacion_final = None
            # Invalida: aviso.
            elif nota is None:
                avisos.append(f"{fila['nombre']}: la nota final tiene que ser de 0 a 10.")
            # Igual a la automatica: no se guarda nada (sigue calculandose sola).
            elif automatica and nota == Decimal(automatica):
                cierres[2].calificacion_final = None
            # Distinta: se guarda la que puso el docente.
            else:
                cierres[2].calificacion_final = nota

        # Si se esta cerrando el cuatrimestre...
        if cerrar:
            # Al cerrar, la calificación calculada queda fija con la fecha de cierre.
            # ...lee las notas del alumno...
            notas = {
                n.categoria_id: n.valor
                for n in NotaEvaluacion.objects.filter(alumno=alumno, materia=materia, cuatrimestre=cuat)
            }
            # ...calcula la nota entera...
            calif = _calificacion_entera(notas, categorias)
            # ...y si hay nota...
            if calif is not None:
                # ...la deja fija en el cierre.
                cierre.calificacion = calif
            # Marca cerrado.
            cierre.cerrado = True
            # Guarda cuando se cerro.
            cierre.fecha_cierre = ahora

        # Guarda los dos cierres en la base.
        cierres[1].save()
        cierres[2].save()

    # Muestra los avisos acumulados.
    for aviso in avisos:
        messages.warning(request, aviso)
    # Cartel final segun la accion.
    if cerrar:
        messages.success(request, f"Cierre del {cuat}° cuatrimestre guardado.")
    else:
        messages.success(request, "Cambios guardados.")
