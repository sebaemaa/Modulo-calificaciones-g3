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
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# --- Django ----------------------------------------------------------------
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

# --- Otros módulos del sistema (solo lectura) -------------------------------
from alumnos.models import Alumno
from asistencia.models import RegistroAsistencia
from cuentas.decoradores import rol_requerido
from docentes.models import Materia

# --- Modelos propios del módulo -------------------------------------------
from .models import (
    CategoriaEvaluacion,
    CierreCuatrimestre,
    ConfirmacionRite,
    InasistenciaMateria,
    NotaEvaluacion,
    PlanillaDatos,
    PublicacionBoletin,
)


# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────

# Meses de cada cuatrimestre (1° = marzo a julio, 2° = agosto a diciembre).
MESES_CUATRIMESTRE = {1: [3, 4, 5, 6, 7], 2: [8, 9, 10, 11, 12]}

# Roles que ven todo el módulo (planillas de todos y boletines siempre).
ROLES_GESTION = ("administrativo", "directivo")

# Asistencia mínima para aprobar una materia.
ASISTENCIA_MINIMA = Decimal("80")

# Nota mínima para aprobar (RITE).
NOTA_APROBACION = 7

# Importar/descargar Excel necesita la librería openpyxl. No está en
# requirements.txt (es un archivo compartido), así que se avisa si falta.
EXCEL_DISPONIBLE = importlib.util.find_spec("openpyxl") is not None


# ─────────────────────────────────────────────
#  HELPERS: ROL, CURSO Y PERMISOS
# ─────────────────────────────────────────────

def _rol(request):
    """Rol del usuario logueado. Los superusuarios cuentan como administrativo."""
    if request.user.is_superuser:
        return "administrativo"
    perfil = getattr(request.user, "perfil", None)
    return perfil.rol if perfil is not None else None


def _docente_logueado(request):
    """Ficha de Docente del usuario logueado, o None si no es docente."""
    perfil = getattr(request.user, "perfil", None)
    if perfil is None or perfil.rol != "docente":
        return None
    return perfil.docente


def _cuat_de_query(request):
    """Cuatrimestre elegido con ?cuat= (1 o 2). Si viene mal, usa el 1°."""
    try:
        cuat = int(request.GET.get("cuat", 1))
    except (TypeError, ValueError):
        return 1
    return cuat if cuat in (1, 2) else 1


def _texto_curso(curso):
    """'5° B' a partir de un Curso."""
    return f"{curso.anio}° {curso.division}"


def _alumnos_del_curso(curso):
    """Alumnos activos de un curso, ordenados por apellido.

    El módulo Alumnos guarda el año y la división en cada alumno (no hay
    relación directa con Curso), así que se filtra por esos dos campos.
    """
    return Alumno.objects.filter(
        anio=curso.anio, division=curso.division, activo=True,
    ).order_by("apellido", "nombre")


def _materias_del_alumno(alumno):
    """Materias del curso del alumno (mismo año y división)."""
    return Materia.objects.filter(
        curso__anio=alumno.anio, curso__division=alumno.division,
    ).select_related("curso", "docente").order_by("nombre")


def _alumno_de_la_materia(materia, alumno_id):
    """Alumno activo del curso de la materia, o None si no pertenece a ese curso."""
    return _alumnos_del_curso(materia.curso).filter(id=alumno_id).first()


def _materia_para_consulta(request, materia_id):
    """Materia que el usuario puede VER, o None.

    - El docente solo ve sus materias.
    - Secretaría y directivo ven las de todos (para imprimir planillas).
    """
    materia = (
        Materia.objects.select_related("curso", "docente")
        .filter(id=materia_id).first()
    )
    if materia is None:
        return None
    if _rol(request) in ROLES_GESTION:
        return materia
    docente = _docente_logueado(request)
    if docente is not None and materia.docente_id == docente.id:
        return materia
    return None


def _materia_del_docente(request, materia_id):
    """Materia que el usuario puede MODIFICAR: solo el docente que la da."""
    docente = _docente_logueado(request)
    if docente is None:
        return None
    return (
        Materia.objects.select_related("curso", "docente")
        .filter(id=materia_id, docente=docente).first()
    )


def _nombre_docente(materia):
    """Nombre y apellido del docente de la materia, o '—' si no tiene."""
    docente = materia.docente
    if docente is None:
        return "—"
    return f"{docente.nombre} {docente.apellido}".strip() or docente.dni


def _categorias(materia):
    """Categorías de evaluación de la materia, en el orden de la grilla."""
    return list(
        CategoriaEvaluacion.objects.filter(materia=materia)
        .order_by("orden", "nombre")
        .values("id", "nombre", "orden", "grupo", "peso")
    )


# ─────────────────────────────────────────────
#  HELPERS: PUBLICACIÓN DEL BOLETÍN
# ─────────────────────────────────────────────

def _boletin_publicado(anio=None):
    """True si secretaría publicó el boletín del año (por defecto, el actual)."""
    anio = anio or timezone.now().year
    return PublicacionBoletin.objects.filter(anio=anio, publicado=True).exists()


def _puede_ver_boletin(request):
    """Secretaría y directivo siempre; alumno y docente solo con el año publicado."""
    return _rol(request) in ROLES_GESTION or _boletin_publicado()


# ─────────────────────────────────────────────
#  HELPERS: NÚMEROS Y FORMATO
# ─────────────────────────────────────────────

def _redondear(valor, decimales=2):
    """Redondea un Decimal (la mitad hacia arriba, como en la escuela)."""
    return valor.quantize(Decimal("1").scaleb(-decimales), rounding=ROUND_HALF_UP)


def _num_limpio(valor):
    """Decimal como texto con punto y sin ceros de más: 8.50 -> '8.5'."""
    if valor is None:
        return None
    texto = str(valor)
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto


def _formato_ar(valor):
    """Decimal con coma decimal (formato argentino): 8.5 -> '8,5'."""
    return None if valor is None else _num_limpio(valor).replace(".", ",")


def _decimal_desde_texto(texto, minimo=None, maximo=None):
    """Convierte lo que escribe el usuario ('7,5', '8') a Decimal.

    Acepta coma o punto. Devuelve None si está vacío, no es un número o
    queda fuera del rango [minimo, maximo].
    """
    texto = str(texto if texto is not None else "").strip().replace(",", ".")
    if not texto:
        return None
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        return None
    if not valor.is_finite():
        return None
    if minimo is not None and valor < minimo:
        return None
    if maximo is not None and valor > maximo:
        return None
    return valor


def _nota_desde_texto(texto):
    """Nota de 0 a 10, o None."""
    return _decimal_desde_texto(texto, minimo=Decimal("0"), maximo=Decimal("10"))


def _inasistencia_desde_texto(texto):
    """Cantidad de inasistencias (0 o más, sin tope), o None."""
    return _decimal_desde_texto(texto, minimo=Decimal("0"))


# ─────────────────────────────────────────────
#  HELPERS: CÁLCULO DE CALIFICACIONES
# ─────────────────────────────────────────────

def _grupos_de_categorias(categorias):
    """Agrupa categorías seguidas que comparten 'grupo' (ej. 'Trabajos prácticos').

    Cada grupo queda como {nombre, peso, cats}. Una categoría sin grupo es
    un grupo de una sola columna. El peso del grupo es la suma de los pesos
    de sus categorías (o None si ninguna tiene peso).
    """
    grupos = []
    for cat in categorias:
        nombre = cat.get("grupo") or ""
        if grupos and nombre and grupos[-1]["nombre"] == nombre:
            grupos[-1]["cats"].append(cat)
        else:
            grupos.append({"nombre": nombre, "cats": [cat]})
    for grupo in grupos:
        pesos = [c["peso"] for c in grupo["cats"] if c["peso"] is not None]
        grupo["peso"] = sum(pesos) if pesos else None
    return grupos


def _calificacion_cuat(notas, categorias):
    """Calificación del cuatrimestre (Decimal con 1 decimal) o None si no hay notas.

    notas = {categoria_id: Decimal}.
    - Sin pesos: promedio simple de las notas cargadas.
    - Con pesos: cada grupo aporta su peso; dentro del grupo, las notas que
      faltan no cuentan (se promedian las cargadas).
    """
    presentes = [notas[c["id"]] for c in categorias if notas.get(c["id"]) is not None]
    if not presentes:
        return None

    if not any(c.get("peso") is not None for c in categorias):
        return _redondear(sum(presentes, Decimal("0")) / len(presentes), 1)

    acumulado = Decimal("0")
    peso_total = Decimal("0")
    for grupo in _grupos_de_categorias(categorias):
        con_nota = [(c, notas[c["id"]]) for c in grupo["cats"] if notas.get(c["id"]) is not None]
        if not con_nota:
            continue
        pesos = [c["peso"] if c["peso"] is not None else Decimal("1") for c, _ in con_nota]
        promedio_grupo = sum(n * p for (_, n), p in zip(con_nota, pesos)) / sum(pesos)
        peso_grupo = grupo["peso"] if grupo["peso"] is not None else Decimal(len(grupo["cats"]))
        acumulado += promedio_grupo * peso_grupo
        peso_total += peso_grupo

    if peso_total == 0:
        return None
    return _redondear(acumulado / peso_total, 1)


def _calificacion_entera(notas, categorias):
    """Calificación del cuatrimestre redondeada a entero (escala 1 a 10), o None."""
    calif = _calificacion_cuat(notas, categorias)
    return _redondear(calif, 0) if calif is not None else None


def _valoracion_preliminar(nota):
    """TEA (7 o más), TEP (5 a 6) o TED (menos de 5) a partir de la nota."""
    if nota is None:
        return ""
    if nota >= 7:
        return "TEA"
    if nota >= 5:
        return "TEP"
    return "TED"


def _estado_materia(nota, asistencia_ok=True):
    """Texto del estado: 'Aprobada', 'A intensificar' o 'No acredita por asistencia'."""
    if nota is None:
        return None
    if not asistencia_ok:
        return "No acredita por asistencia"
    return "Aprobada" if nota >= NOTA_APROBACION else "A intensificar"


def _datos_cuatrimestre(notas, categorias, cierre):
    """Datos de un cuatrimestre: notas por columna, valoración y calificación.

    Si el docente ya cerró el cuatrimestre, manda la calificación del cierre.
    Si eligió una valoración a mano, manda esa; si no, se deriva de la nota.
    """
    calif = _calificacion_entera(notas, categorias)
    if cierre is not None and cierre.calificacion is not None:
        calif = _redondear(cierre.calificacion, 0)

    if cierre is not None and cierre.valoracion_preliminar:
        valoracion = cierre.valoracion_preliminar
    else:
        valoracion = _valoracion_preliminar(calif)

    return {
        "valores": [_num_limpio(notas.get(c["id"])) or "" for c in categorias],
        "valoracion": valoracion,
        "calificacion": str(calif) if calif is not None else "",
        "aprobada": calif is not None and calif >= NOTA_APROBACION,
        "tiene_calificacion": calif is not None,
    }


def _final_automatico(d1, d2, cierre1):
    """Promedio entero del 1° cuatrimestre (o su intensificación) y el 2°.

    Devuelve '' si todavía falta la calificación de alguno de los dos.
    """
    if not d1["calificacion"] or not d2["calificacion"]:
        return ""
    nota1 = Decimal(d1["calificacion"])
    if cierre1 is not None and cierre1.intensificacion and cierre1.calificacion_final is not None:
        nota1 = cierre1.calificacion_final
    nota2 = Decimal(d2["calificacion"])
    return _num_limpio(_redondear((nota1 + nota2) / 2, 0))


def _calificacion_final(d1, d2, cierre1, cierre2):
    """Nota final del año: la que cargó el docente a mano o, si no hay, la automática."""
    if cierre2 is not None and cierre2.calificacion_final is not None:
        return _num_limpio(cierre2.calificacion_final)
    return _final_automatico(d1, d2, cierre1)


def _intensificacion(cierre1):
    """Nota de intensificación del 1° cuatrimestre (texto) o ''."""
    if cierre1 is not None and cierre1.intensificacion and cierre1.calificacion_final is not None:
        return _num_limpio(cierre1.calificacion_final)
    return ""


# ─────────────────────────────────────────────
#  HELPERS: ASISTENCIA (se lee del módulo Asistencia)
# ─────────────────────────────────────────────

def _faltas(registros):
    """Faltas de un conjunto de registros: Ausente = 1 y Tardanza = 0,5."""
    ausentes = registros.filter(estado="A").count()
    tardanzas = registros.filter(estado="T").count()
    return Decimal(ausentes) + Decimal(tardanzas) / 2


def _inasistencias_alumno_cuat(alumno, cuat):
    """Inasistencias totales del alumno en el cuatrimestre (todas las materias)."""
    registros = RegistroAsistencia.objects.filter(
        alumno=alumno, fecha__month__in=MESES_CUATRIMESTRE[cuat],
    )
    return _redondear(_faltas(registros))


def _inasistencias_materia_cuat(alumno_id, materia, cuat):
    """Inasistencias del alumno en UNA materia y un cuatrimestre."""
    registros = RegistroAsistencia.objects.filter(
        alumno_id=alumno_id, materia=materia, fecha__month__in=MESES_CUATRIMESTRE[cuat],
    )
    return _redondear(_faltas(registros))


def _asistencia_materia(alumno_id, materia):
    """Asistencia anual del alumno en una materia, o None si no hay registros.

    Total de clases = fechas distintas con algún registro de la materia.
    Devuelve {clases, faltas, porcentaje, suficiente}; 'suficiente' es la
    regla del 80 %: sin eso la materia no se aprueba.
    """
    registros = RegistroAsistencia.objects.filter(materia=materia)
    clases = registros.values("fecha").distinct().count()
    if not clases:
        return None
    faltas = _faltas(registros.filter(alumno_id=alumno_id))
    porcentaje = _redondear((clases - faltas) / clases * 100, 1)
    return {
        "clases": clases,
        "faltas": _redondear(faltas, 1),
        "porcentaje": porcentaje,
        "suficiente": porcentaje >= ASISTENCIA_MINIMA,
    }


def _clases_dadas(materia, cuat):
    """Clases efectivamente dadas en el cuatrimestre (días con asistencia tomada)."""
    return RegistroAsistencia.objects.filter(
        materia=materia, fecha__month__in=MESES_CUATRIMESTRE[cuat],
    ).values("fecha").distinct().count()


# ─────────────────────────────────────────────
#  HELPERS: CIERRE DEL CUATRIMESTRE (uno por materia)
# ─────────────────────────────────────────────

def _fecha_cierre(materia, cuat):
    """Fecha de cierre ('30/07/2026') si el cuatrimestre de la materia está cerrado.

    Devuelve None si sigue abierto. Mientras está cerrado no se pueden cambiar
    las notas: el docente lo reabre desde la planilla si necesita corregir.
    """
    cerrados = CierreCuatrimestre.objects.filter(materia=materia, cuatrimestre=cuat, cerrado=True)
    if not cerrados.exists():
        return None
    ultimo = cerrados.exclude(fecha_cierre=None).order_by("-fecha_cierre").first()
    return timezone.localtime(ultimo.fecha_cierre).strftime("%d/%m/%Y") if ultimo else "sin fecha"


def _aviso_cerrado(cuat):
    """Mensaje que se muestra cuando se intenta cambiar un cuatrimestre cerrado."""
    return f"El {cuat}° cuatrimestre está cerrado. Para cambiar notas, reabrilo desde la planilla."


# ─────────────────────────────────────────────
#  MENÚ Y PUBLICACIÓN ANUAL DEL BOLETÍN
# ─────────────────────────────────────────────

@rol_requerido("alumno", "docente", "administrativo", "directivo")
def menu(request):
    """Inicio del módulo: cada rol ve su propia pantalla."""
    cuat = _cuat_de_query(request)
    anio = timezone.now().year
    contexto = {
        "cuat": cuat,
        "ciclo_lectivo": anio,
        "boletin_publicado": _boletin_publicado(anio),
    }

    perfil = getattr(request.user, "perfil", None)
    rol = _rol(request)

    if rol == "docente" and perfil.docente is not None:
        contexto.update(_datos_menu_docente(perfil.docente, cuat))
        return render(request, "calificaciones/menu_docente.html", contexto)

    if rol == "alumno" and perfil.alumno is not None:
        contexto.update(_datos_menu_alumno(perfil.alumno, cuat))
        return render(request, "calificaciones/menu_alumno.html", contexto)

    # Secretaría, directivo y superusuarios.
    contexto.update(_datos_menu_gestion())
    contexto["puede_publicar_boletin"] = rol in ROLES_GESTION
    return render(request, "calificaciones/menu.html", contexto)


@rol_requerido("administrativo", "directivo")
@require_POST
def publicar_boletines(request):
    """Interruptor anual: publica u oculta el boletín de este año."""
    anio = timezone.now().year
    publicacion, _ = PublicacionBoletin.objects.get_or_create(anio=anio)
    publicacion.publicado = not publicacion.publicado
    publicacion.fecha_publicacion = timezone.now() if publicacion.publicado else None
    publicacion.usuario = request.user.get_username()
    publicacion.save()

    if publicacion.publicado:
        messages.success(request, f"Boletines {anio} publicados. Los alumnos ya pueden ver su boletín.")
    else:
        messages.success(request, f"Boletines {anio} ocultos. Los alumnos ven solo su resumen de notas.")
    return redirect("calificaciones_menu")


def _datos_menu_gestion():
    """Todas las materias con su docente, para ver o imprimir cada planilla."""
    materias = (
        Materia.objects.select_related("docente", "curso")
        .order_by("docente__apellido", "docente__nombre", "nombre")
    )
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


def _datos_menu_docente(docente, cuat):
    """Materias del docente con el porcentaje de notas cargadas en el cuatrimestre."""
    materias = (
        Materia.objects.filter(docente=docente)
        .select_related("curso")
        .order_by("nombre", "curso__anio", "curso__division")
    )

    filas = []
    for m in materias:
        cant_alumnos = _alumnos_del_curso(m.curso).count()
        cant_categorias = CategoriaEvaluacion.objects.filter(materia=m).count()
        esperadas = cant_alumnos * cant_categorias  # una nota por alumno y categoría

        pct = None
        if esperadas:
            cargadas = (
                NotaEvaluacion.objects.filter(materia=m, cuatrimestre=cuat)
                .values("alumno_id", "categoria_id").distinct().count()
            )
            pct = min(100, int(cargadas * 100 / esperadas))

        filas.append({
            "id": m.id,
            "nombre": m.nombre,
            "curso": _texto_curso(m.curso),
            "estudiantes": cant_alumnos,
            "pct": pct,
            "completo": pct == 100,
            "fecha_cierre": _fecha_cierre(m, cuat),  # None = cuatrimestre abierto
        })

    return {
        "materias": filas,
        "total_materias": len(filas),
        "sin_cargar": sum(1 for f in filas if not f["completo"]),
        "cerradas": sum(1 for f in filas if f["fecha_cierre"]),
        "excel_disponible": EXCEL_DISPONIBLE,
    }


def _datos_menu_alumno(alumno, cuat):
    """'Mis notas': calificación, valoración y estado de cada materia del alumno."""
    cierres = {
        c.materia_id: c
        for c in CierreCuatrimestre.objects.filter(alumno=alumno, cuatrimestre=cuat)
    }

    filas = []
    calificaciones = []
    for materia in _materias_del_alumno(alumno):
        notas = {
            n.categoria_id: n.valor
            for n in NotaEvaluacion.objects.filter(alumno=alumno, materia=materia, cuatrimestre=cuat)
        }
        datos = _datos_cuatrimestre(notas, _categorias(materia), cierres.get(materia.id))
        calif = Decimal(datos["calificacion"]) if datos["calificacion"] else None
        if calif is not None:
            calificaciones.append(calif)

        asistencia = _asistencia_materia(alumno.id, materia)
        asistencia_ok = asistencia is None or asistencia["suficiente"]

        filas.append({
            "materia": materia.nombre,
            "valoracion": datos["valoracion"],
            "calificacion": datos["calificacion"],
            "estado": _estado_materia(calif, asistencia_ok),
            "aprobada": datos["aprobada"] and asistencia_ok,
        })

    promedio = None
    if calificaciones:
        promedio = _formato_ar(_redondear(sum(calificaciones) / len(calificaciones), 1))

    return {
        "nombre": f"{alumno.apellido}, {alumno.nombre}",
        "curso": f"{alumno.anio}° {alumno.division}",
        "materias": filas,
        "promedio_general": promedio,
        "inasistencias": _formato_ar(_inasistencias_alumno_cuat(alumno, cuat)),
    }


# ─────────────────────────────────────────────
#  BOLETÍN (RITE)
# ─────────────────────────────────────────────

@rol_requerido("docente", "administrativo", "directivo")
def alumno_seleccionar(request):
    """Buscador de alumno para abrir su boletín (el docente ve solo sus cursos)."""
    alumnos = _alumnos_que_puede_ver(request).order_by("anio", "division", "apellido", "nombre")
    return render(request, "calificaciones/alumno_seleccionar.html", {
        "alumnos": alumnos,
        "boletin_publicado": _boletin_publicado(),
        "puede_ver": _puede_ver_boletin(request),
    })


def _alumnos_que_puede_ver(request):
    """Alumnos cuyo boletín puede abrir el usuario.

    Secretaría y directivo: todos. Docente: solo los de los cursos donde da
    alguna materia.
    """
    alumnos = Alumno.objects.filter(activo=True)
    if _rol(request) != "docente":
        return alumnos
    docente = _docente_logueado(request)
    cursos = Materia.objects.filter(docente=docente).values_list("curso__anio", "curso__division").distinct()
    filtro = Q(pk__in=[])  # arranca sin ningún alumno
    for anio, division in cursos:
        filtro |= Q(anio=anio, division=division)
    return alumnos.filter(filtro)


def _alumno_a_mostrar(request):
    """El alumno ve SIEMPRE su propio boletín; los demás roles eligen con alumno_id."""
    perfil = getattr(request.user, "perfil", None)
    if perfil is not None and perfil.rol == "alumno":
        return perfil.alumno
    alumno_id = request.POST.get("alumno_id") or request.GET.get("alumno_id")
    if not alumno_id or not str(alumno_id).isdigit():
        return None
    alumno = _alumnos_que_puede_ver(request).filter(id=alumno_id).first()
    if alumno is None:
        messages.error(request, "Solo podés ver el boletín de alumnos de tus cursos.")
    return alumno


def _puede_firmar(request, tipo):
    """Quién registra cada firma del boletín.

    - Estudiante: el propio alumno.
    - Adulta/o responsable: el docente del curso, secretaría o directivo.
    - Director/a: solo el equipo directivo.
    """
    rol = _rol(request)
    if tipo == "estudiante":
        return rol == "alumno"
    if tipo == "director":
        return rol == "directivo" or request.user.is_superuser
    return rol in ("docente", "administrativo", "directivo")


def _datos_rite(alumno, request):
    """Datos del boletín: frente (calificaciones) y dorso (intensificación,
    asistencia y firmas)."""
    notas = {}  # {(materia_id, cuat): {categoria_id: valor}}
    for n in NotaEvaluacion.objects.filter(alumno=alumno).order_by("id"):
        notas.setdefault((n.materia_id, n.cuatrimestre), {})[n.categoria_id] = n.valor
    cierres = {
        (c.materia_id, c.cuatrimestre): c
        for c in CierreCuatrimestre.objects.filter(alumno=alumno)
    }

    materias = list(_materias_del_alumno(alumno))
    filas = []
    intensifican = []
    for m in materias:
        categorias = _categorias(m)
        cierre1 = cierres.get((m.id, 1))
        cierre2 = cierres.get((m.id, 2))
        d1 = _datos_cuatrimestre(notas.get((m.id, 1), {}), categorias, cierre1)
        d2 = _datos_cuatrimestre(notas.get((m.id, 2), {}), categorias, cierre2)

        asistencia = _asistencia_materia(alumno.id, m)
        asistencia_ok = asistencia is None or asistencia["suficiente"]

        # Promedio anual: solo si los dos cuatrimestres están aprobados y la
        # asistencia alcanza.
        promedio_anual = ""
        if asistencia_ok and d1["aprobada"] and d2["aprobada"]:
            suma = Decimal(d1["calificacion"]) + Decimal(d2["calificacion"])
            promedio_anual = _formato_ar(_redondear(suma / 2, 1))

        filas.append({
            "materia": m.nombre,
            "anio": f"{m.curso.anio}°",
            "cursada": cierre1.cursada if cierre1 else "C",
            "val1": d1["valoracion"],
            "calif1": d1["calificacion"],
            "val2": d2["valoracion"],
            "calif2": d2["calificacion"],
            "promedio_anual": promedio_anual,
            "intensificacion": _intensificacion(cierre1),
            "dic": _num_limpio(cierre2.nota_diciembre) if cierre2 and cierre2.nota_diciembre is not None else "",
            "feb": _num_limpio(cierre2.nota_febrero) if cierre2 and cierre2.nota_febrero is not None else "",
            "no_acredita": not asistencia_ok,
        })

        if cierre1 is not None and cierre1.intensificacion and asistencia_ok:
            intensifican.append({
                "materia": m.nombre,
                "anio": f"{m.curso.anio}°",
                "calif_final": _num_limpio(cierre1.calificacion_final) or "",
            })

    # El dorso oficial tiene 9 renglones de intensificación.
    while len(intensifican) < 9:
        intensifican.append({"materia": "", "anio": "", "calif_final": ""})

    # Asistencia del dorso: días con registro e inasistencias de cada cuatrimestre.
    dias = {}
    inas = {}
    for c in (1, 2):
        dias[c] = RegistroAsistencia.objects.filter(
            alumno=alumno, fecha__month__in=MESES_CUATRIMESTRE[c],
        ).values("fecha").distinct().count()
        inas[c] = _inasistencias_alumno_cuat(alumno, c)

    # Firmas: quién tomó conocimiento en cada cuatrimestre.
    firmadas = set(ConfirmacionRite.objects.filter(alumno=alumno).values_list("cuatrimestre", "tipo"))
    firmas = []
    for tipo, nombre in ConfirmacionRite.TIPO_CHOICES:
        firmas.append({
            "tipo": tipo,
            "nombre": nombre,
            "c1": (1, tipo) in firmadas,
            "c2": (2, tipo) in firmadas,
            # [(1, firmada?), (2, firmada?)] para dibujar una celda por cuatrimestre.
            "estados": [(c, (c, tipo) in firmadas) for c in (1, 2)],
            "puede_firmar": _puede_firmar(request, tipo),
        })

    # Preceptor/a: el que figura en alguna planilla del curso del alumno.
    preceptor = (
        PlanillaDatos.objects.filter(materia__in=materias)
        .exclude(preceptor="").values_list("preceptor", flat=True).first()
    )

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
        "dias_total": dias[1] + dias[2],
        "inasistencias": {c: _formato_ar(inas[c]) for c in (1, 2)},
        "total_inasistencias": _formato_ar(inas[1] + inas[2]),
        "firmas": firmas,
        "es_alumno": _rol(request) == "alumno",
        "ciclo_lectivo": timezone.now().year,
    }


@rol_requerido("alumno", "docente", "administrativo", "directivo")
def alumno_ver_boletin(request):
    """Boletín (RITE) de un alumno. Bloqueado hasta que se publique el año."""
    if not _puede_ver_boletin(request):
        messages.warning(request, "El boletín se habilita a fin de año. Mientras tanto podés consultar las notas en el inicio del módulo.")
        return redirect("calificaciones_menu")

    alumno = _alumno_a_mostrar(request)
    if alumno is None:
        return redirect("alumno_seleccionar")
    return render(request, "calificaciones/boletin.html", _datos_rite(alumno, request))


@rol_requerido("alumno", "docente", "administrativo", "directivo")
@require_POST
def confirmar_rite(request):
    """Registra que alguien tomó conocimiento del boletín (quién y cuándo)."""
    if not _puede_ver_boletin(request):
        messages.warning(request, "El boletín se habilita a fin de año. Todavía no se pueden registrar firmas.")
        return redirect("calificaciones_menu")

    alumno = _alumno_a_mostrar(request)
    if alumno is None:
        return redirect("alumno_seleccionar")

    destino = redirect(f"{reverse('alumno_ver_boletin')}?alumno_id={alumno.id}")
    tipo = request.POST.get("tipo", "").strip()
    cuat = request.POST.get("cuat", "")
    if tipo not in dict(ConfirmacionRite.TIPO_CHOICES) or cuat not in ("1", "2"):
        return destino

    if not _puede_firmar(request, tipo):
        nombre = dict(ConfirmacionRite.TIPO_CHOICES)[tipo]
        messages.error(request, f"Tu usuario no puede registrar la firma de {nombre}.")
        return destino

    ConfirmacionRite.objects.update_or_create(
        alumno=alumno, cuatrimestre=int(cuat), tipo=tipo,
        defaults={"usuario": request.user.get_username()},
    )
    messages.success(request, "Firma registrada.")
    return destino
