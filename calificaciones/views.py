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
    BoletinConfig,
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


def _calificacion_final(d1, d2, cierre1, cierre2):
    """Nota final del año (texto) o '' si todavía falta algún cuatrimestre.

    - Si el cierre del 2° cuatrimestre tiene una final cargada, se usa esa.
    - Si no, es el promedio entero del 1° (o su intensificación) y el 2°.
    """
    if cierre2 is not None and cierre2.calificacion_final is not None:
        return _num_limpio(cierre2.calificacion_final)
    if not d1["calificacion"] or not d2["calificacion"]:
        return ""

    nota1 = Decimal(d1["calificacion"])
    if cierre1 is not None and cierre1.intensificacion and cierre1.calificacion_final is not None:
        nota1 = cierre1.calificacion_final
    nota2 = Decimal(d2["calificacion"])
    return _num_limpio(_redondear((nota1 + nota2) / 2, 0))


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
        })

    config = BoletinConfig.objects.filter(cuatrimestre=cuat).first()
    fecha_cierre = config.fecha_publicacion if config else None

    return {
        "materias": filas,
        "total_materias": len(filas),
        "sin_cargar": sum(1 for f in filas if not f["completo"]),
        "fecha_cierre": fecha_cierre.strftime("%d/%m/%Y") if fecha_cierre else None,
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
#  DOCENTE: CARGAR NOTAS (grilla con guardado automático)
# ─────────────────────────────────────────────

@rol_requerido("docente")
@ensure_csrf_cookie
def profesor_cargar_notas(request, cuat, materia_id):
    """Grilla de notas del cuatrimestre: cada celda se guarda sola al cambiarla."""
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "No podés cargar notas en esa materia.")
        return redirect("calificaciones_menu")

    categorias = _categorias(materia)
    if not categorias:
        messages.warning(request, "Primero creá al menos una categoría de evaluación para esta materia.")
        return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)

    # Datos para que el JavaScript calcule igual que el servidor.
    grupos = _grupos_de_categorias(categorias)
    for grupo in grupos:
        peso_grupo = grupo["peso"] if grupo["peso"] is not None else Decimal(len(grupo["cats"]))
        for cat in grupo["cats"]:
            cat["grupo_key"] = grupo["nombre"] or f"_cat{cat['id']}"
            cat["peso_js"] = _num_limpio(cat["peso"] if cat["peso"] is not None else Decimal("1"))
            cat["peso_grupo_js"] = _num_limpio(peso_grupo)

    notas = {}  # {(alumno_id, categoria_id): valor}
    for n in NotaEvaluacion.objects.filter(materia=materia, cuatrimestre=cuat).order_by("id"):
        notas[(n.alumno_id, n.categoria_id)] = n.valor
    cierres = {
        c.alumno_id: c
        for c in CierreCuatrimestre.objects.filter(materia=materia, cuatrimestre=cuat)
    }
    inasistencias = {
        i.alumno_id: i.cantidad
        for i in InasistenciaMateria.objects.filter(materia=materia, cuatrimestre=cuat)
    }

    filas = []
    for alumno in _alumnos_del_curso(materia.curso):
        notas_alumno = {
            cat["id"]: notas[(alumno.id, cat["id"])]
            for cat in categorias if (alumno.id, cat["id"]) in notas
        }
        datos = _datos_cuatrimestre(notas_alumno, categorias, cierres.get(alumno.id))
        calif = Decimal(datos["calificacion"]) if datos["calificacion"] else None

        asistencia = _asistencia_materia(alumno.id, materia)
        asistencia_ok = asistencia is None or asistencia["suficiente"]

        # Inasistencias: la carga del docente o, si no hay, las del módulo Asistencia.
        inas = inasistencias.get(alumno.id)
        if inas is None:
            inas = _inasistencias_materia_cuat(alumno.id, materia, cuat)

        filas.append({
            "id": alumno.id,
            "nombre": f"{alumno.apellido}, {alumno.nombre}",
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

    return render(request, "calificaciones/cargar_notas.html", {
        "cuat": cuat,
        "materia": materia,
        "curso": _texto_curso(materia.curso),
        "filas": filas,
        "categorias": categorias,
        "grupos": grupos,
        "tiene_grupos": any(g["nombre"] for g in grupos),
        "con_pesos": any(c["peso"] is not None for c in categorias),
    })


def _validar_ajax(request, cuat, materia_id):
    """Chequeos comunes de los guardados automáticos.

    Devuelve (materia, alumno, None) si todo está bien, o (None, None, respuesta
    de error) si algo falla.
    """
    if request.method != "POST":
        return None, None, JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    if cuat not in (1, 2):
        return None, None, JsonResponse({"ok": False, "error": "Cuatrimestre inválido"}, status=400)
    materia = _materia_del_docente(request, materia_id)
    if materia is None:
        return None, None, JsonResponse({"ok": False, "error": "Esa materia no es tuya"}, status=403)
    alumno = _alumno_de_la_materia(materia, request.POST.get("alumno_id") or 0)
    if alumno is None:
        return None, None, JsonResponse({"ok": False, "error": "Alumno no encontrado"}, status=404)
    return materia, alumno, None


@rol_requerido("docente")
def profesor_guardar_nota(request, cuat, materia_id):
    """Guardado automático de una celda de nota. Celda vacía = borrar la nota."""
    materia, alumno, error = _validar_ajax(request, cuat, materia_id)
    if error:
        return error

    categoria = CategoriaEvaluacion.objects.filter(
        id=request.POST.get("cat_id") or 0, materia=materia,
    ).first()
    if categoria is None:
        return JsonResponse({"ok": False, "error": "Categoría no encontrada"}, status=404)

    texto = request.POST.get("valor", "").strip()
    filtro = {"alumno": alumno, "materia": materia, "categoria": categoria, "cuatrimestre": cuat}
    if texto == "":
        NotaEvaluacion.objects.filter(**filtro).delete()
    else:
        valor = _nota_desde_texto(texto)
        if valor is None:
            return JsonResponse({"ok": False, "error": f"'{texto}' no es una nota válida (0 a 10)"}, status=400)
        # Si por algún motivo hubiera notas repetidas en la celda, quedan en una sola.
        NotaEvaluacion.objects.filter(**filtro).delete()
        NotaEvaluacion.objects.create(valor=valor, **filtro)

    # Devuelve la calificación recalculada para refrescar la fila.
    notas = {
        n.categoria_id: n.valor
        for n in NotaEvaluacion.objects.filter(alumno=alumno, materia=materia, cuatrimestre=cuat)
    }
    calif = _calificacion_entera(notas, _categorias(materia))
    asistencia = _asistencia_materia(alumno.id, materia)
    asistencia_ok = asistencia is None or asistencia["suficiente"]
    return JsonResponse({
        "ok": True,
        "calificacion": str(calif) if calif is not None else "",
        "estado_materia": _estado_materia(calif, asistencia_ok),
    })


@rol_requerido("docente")
def profesor_guardar_valoracion(request, cuat, materia_id):
    """Guardado automático de la valoración preliminar (TEA / TEP / TED)."""
    materia, alumno, error = _validar_ajax(request, cuat, materia_id)
    if error:
        return error

    valoracion = request.POST.get("valoracion", "").strip().upper()
    if valoracion not in ("TEA", "TEP", "TED", ""):
        return JsonResponse({"ok": False, "error": "Valoración inválida"}, status=400)

    CierreCuatrimestre.objects.update_or_create(
        alumno=alumno, materia=materia, cuatrimestre=cuat,
        defaults={"valoracion_preliminar": valoracion},
    )
    return JsonResponse({"ok": True, "valoracion": valoracion})


@rol_requerido("docente")
def profesor_guardar_inasistencia(request, cuat, materia_id):
    """Guardado automático de las inasistencias del alumno en la materia."""
    materia, alumno, error = _validar_ajax(request, cuat, materia_id)
    if error:
        return error

    texto = request.POST.get("valor", "").strip()
    filtro = {"alumno": alumno, "materia": materia, "cuatrimestre": cuat}
    if texto == "":
        InasistenciaMateria.objects.filter(**filtro).delete()
        return JsonResponse({"ok": True, "borrado": True})

    cantidad = _inasistencia_desde_texto(texto)
    if cantidad is None:
        return JsonResponse({"ok": False, "error": f"'{texto}' no es una cantidad válida"}, status=400)
    InasistenciaMateria.objects.update_or_create(**filtro, defaults={"cantidad": cantidad})
    return JsonResponse({"ok": True, "cantidad": _formato_ar(cantidad)})


# ─────────────────────────────────────────────
#  DOCENTE: CATEGORÍAS DE EVALUACIÓN
# ─────────────────────────────────────────────

def _peso_desde_texto(texto):
    """Peso % de una categoría (mayor a 0 y hasta 100), o None si está vacío.

    Lanza ValueError con el motivo si el texto no sirve.
    """
    if not (texto or "").strip():
        return None
    peso = _decimal_desde_texto(texto)
    if peso is None:
        raise ValueError("no es un número")
    if peso <= 0 or peso > 100:
        raise ValueError("tiene que estar entre 0 y 100")
    return peso


def _datos_categoria(request):
    """Lee nombre, grupo y peso del formulario. Devuelve (datos, error)."""
    nombre = request.POST.get("nombre", "").strip()
    if not nombre:
        return None, "El nombre no puede estar vacío."
    try:
        peso = _peso_desde_texto(request.POST.get("peso", ""))
    except ValueError as motivo:
        return None, f"El peso '{request.POST.get('peso')}' {motivo}."
    return {"nombre": nombre, "grupo": request.POST.get("grupo", "").strip(), "peso": peso}, None


@rol_requerido("docente")
def profesor_categorias(request, cuat, materia_id):
    """Lista de categorías con el formulario para agregar o editar."""
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    categorias = _categorias(materia)
    edit_id = request.GET.get("editar")
    editando = next((c for c in categorias if str(c["id"]) == edit_id), None)
    return render(request, "calificaciones/gestionar_categorias.html", {
        "cuat": cuat,
        "materia": materia,
        "curso": _texto_curso(materia.curso),
        "categorias": categorias,
        "editando": editando,
    })


@rol_requerido("docente")
@require_POST
def profesor_agregar_categoria(request, cuat, materia_id):
    """Crea una categoría nueva al final de la grilla."""
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    datos, error = _datos_categoria(request)
    if error:
        messages.error(request, error)
    else:
        ultimo = CategoriaEvaluacion.objects.filter(materia=materia).order_by("-orden").first()
        orden = (ultimo.orden if ultimo else 0) + 1
        CategoriaEvaluacion.objects.create(materia=materia, orden=orden, **datos)
        messages.success(request, f"Categoría '{datos['nombre']}' creada.")
    return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)


@rol_requerido("docente")
@require_POST
def profesor_editar_categoria(request, cuat, materia_id, cat_id):
    """Cambia nombre, grupo y peso de una categoría."""
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    categoria = get_object_or_404(CategoriaEvaluacion, id=cat_id, materia=materia)
    datos, error = _datos_categoria(request)
    if error:
        messages.error(request, error)
    else:
        for campo, valor in datos.items():
            setattr(categoria, campo, valor)
        categoria.save()
        messages.success(request, "Categoría actualizada.")
    return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)


@rol_requerido("docente")
@require_POST
def profesor_eliminar_categoria(request, cuat, materia_id, cat_id):
    """Borra una categoría y sus notas (solo por POST, con confirmación)."""
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    categoria = get_object_or_404(CategoriaEvaluacion, id=cat_id, materia=materia)
    categoria.delete()
    messages.success(request, f"Categoría '{categoria.nombre}' eliminada.")
    return redirect("profesor_categorias", cuat=cuat, materia_id=materia.id)


# ─────────────────────────────────────────────
#  DOCENTE: IMPORTAR NOTAS DESDE EXCEL
# ─────────────────────────────────────────────

def _clave_excel(cuat, materia):
    """Clave de sesión donde se guarda el Excel leído hasta que se confirma."""
    return f"excel_{cuat}_{materia.id}"


def _buscar_alumno_por_nombre(materia, texto):
    """Alumno del curso por 'Apellido, Nombre', o por apellido/nombre solo."""
    alumnos = _alumnos_del_curso(materia.curso)
    if ", " in texto:
        apellido, _, nombre = texto.partition(", ")
        alumno = alumnos.filter(apellido__iexact=apellido.strip(), nombre__iexact=nombre.strip()).first()
        if alumno:
            return alumno
    return alumnos.filter(Q(nombre__iexact=texto) | Q(apellido__iexact=texto)).first()


@rol_requerido("docente")
def profesor_cargar_excel(request, cuat, materia_id):
    """Paso 1: subir el Excel y mostrar la vista previa."""
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    contexto = {"cuat": cuat, "materia": materia, "curso": _texto_curso(materia.curso)}
    if request.method != "POST":
        return render(request, "calificaciones/cargar_excel.html", contexto)

    archivo = request.FILES.get("archivo")
    if archivo is None:
        messages.error(request, "Elegí un archivo Excel para subir.")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    try:
        import openpyxl
    except ImportError:
        messages.error(request, "Falta instalar la librería openpyxl (pip install openpyxl).")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    try:
        hoja = openpyxl.load_workbook(archivo, read_only=True, data_only=True).active
        filas_excel = list(hoja.iter_rows(values_only=True))
    except Exception:
        messages.error(request, "No se pudo leer el archivo. Tiene que ser un Excel (.xlsx).")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    if not filas_excel:
        messages.error(request, "El archivo está vacío.")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    encabezados = [str(h).strip() if h is not None else "" for h in filas_excel[0]]
    categorias = {c["nombre"]: c for c in _categorias(materia)}
    # Columnas del Excel que coinciden con una categoría: {índice: categoría}.
    columnas = {i: categorias[h] for i, h in enumerate(encabezados) if i > 0 and h in categorias}

    vista_previa = []
    para_guardar = []
    for fila in filas_excel[1:]:
        if not fila or not fila[0]:
            continue
        nombre = str(fila[0]).strip()
        alumno = _buscar_alumno_por_nombre(materia, nombre)
        notas = {}
        for i, cat in columnas.items():
            valor = fila[i] if i < len(fila) else None
            notas[cat["id"]] = "" if valor is None else str(valor).strip()
        vista_previa.append({
            "nombre": nombre,
            "encontrado": alumno is not None,
            "valores": [notas.get(cat["id"]) or "—" for cat in columnas.values()],
        })
        if alumno is not None:
            para_guardar.append({"alumno_id": alumno.id, "notas": {str(k): v for k, v in notas.items()}})

    request.session[_clave_excel(cuat, materia)] = para_guardar
    contexto.update({
        "columnas": [cat["nombre"] for cat in columnas.values()],
        "vista_previa": vista_previa,
        "hay_para_guardar": bool(para_guardar),
    })
    return render(request, "calificaciones/confirmar_excel.html", contexto)


@rol_requerido("docente")
@require_POST
def profesor_confirmar_excel(request, cuat, materia_id):
    """Paso 2: guardar las notas de la vista previa confirmada."""
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    filas = request.session.pop(_clave_excel(cuat, materia), None)
    if not filas:
        messages.error(request, "No se encontraron datos del Excel. Volvé a subir el archivo.")
        return redirect("profesor_cargar_excel", cuat=cuat, materia_id=materia.id)

    categorias = {str(c["id"]): c["id"] for c in _categorias(materia)}
    guardadas = 0
    omitidas = 0
    for fila in filas:
        alumno = _alumno_de_la_materia(materia, fila["alumno_id"])
        if alumno is None:
            continue
        for cat_id, texto in fila["notas"].items():
            if cat_id not in categorias or texto == "":
                continue
            valor = _nota_desde_texto(texto)
            if valor is None:
                omitidas += 1
                continue
            filtro = {"alumno": alumno, "materia": materia,
                      "categoria_id": categorias[cat_id], "cuatrimestre": cuat}
            NotaEvaluacion.objects.filter(**filtro).delete()
            NotaEvaluacion.objects.create(valor=valor, **filtro)
            guardadas += 1

    messages.success(request, f"Se cargaron {guardadas} notas desde Excel.")
    if omitidas:
        messages.warning(request, f"Se omitieron {omitidas} valores que no eran notas de 0 a 10.")
    return redirect("profesor_cargar_notas", cuat=cuat, materia_id=materia.id)


@rol_requerido("docente")
def profesor_descargar_plantilla(request, cuat, materia_id):
    """Descarga un Excel con los alumnos y una columna por categoría."""
    materia = _materia_del_docente(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "Esa materia no es tuya.")
        return redirect("calificaciones_menu")

    try:
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        messages.error(request, "Falta instalar la librería openpyxl (pip install openpyxl).")
        return redirect("profesor_cargar_notas", cuat=cuat, materia_id=materia.id)

    categorias = _categorias(materia)
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = f"{cuat}° cuatrimestre"

    borde = Border(*(Side(style="thin"),) * 4)
    encabezado = ["Alumno"] + [c["nombre"] for c in categorias]
    for col, texto in enumerate(encabezado, start=1):
        celda = hoja.cell(row=1, column=col, value=texto)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        celda.alignment = Alignment(horizontal="center")
        celda.border = borde
        hoja.column_dimensions[get_column_letter(col)].width = 30 if col == 1 else 18

    for fila, alumno in enumerate(_alumnos_del_curso(materia.curso), start=2):
        hoja.cell(row=fila, column=1, value=f"{alumno.apellido}, {alumno.nombre}")
        for col in range(1, len(encabezado) + 1):
            hoja.cell(row=fila, column=col).border = borde

    respuesta = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    nombre_archivo = f"plantilla_{materia.nombre}_{_texto_curso(materia.curso)}_{cuat}cuat.xlsx"
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo.replace(" ", "_")}"'
    libro.save(respuesta)
    return respuesta


# ─────────────────────────────────────────────
#  PLANILLA DE CALIFICACIONES (hoja oficial imprimible)
# ─────────────────────────────────────────────

@rol_requerido("docente", "administrativo", "directivo")
def profesor_planilla(request, cuat, materia_id):
    """Planilla oficial de la materia, con los dos cuatrimestres.

    El docente de la materia la completa y la guarda; secretaría y directivo
    la ven en modo lectura para imprimirla.
    """
    materia = _materia_para_consulta(request, materia_id)
    if materia is None or cuat not in (1, 2):
        messages.error(request, "No podés consultar esa materia.")
        return redirect("calificaciones_menu")

    puede_editar = _materia_del_docente(request, materia.id) is not None

    if request.method == "POST":
        if not puede_editar:
            messages.error(request, "Solo el docente de la materia puede guardar los cambios.")
            return redirect("profesor_planilla", cuat=cuat, materia_id=materia.id)
        _guardar_planilla(request, materia, cuat)
        return redirect("profesor_planilla", cuat=cuat, materia_id=materia.id)

    categorias = _categorias(materia)
    filas = _filas_planilla(materia, categorias, cuat)
    datos_planilla = PlanillaDatos.objects.filter(materia=materia).first()

    # La hoja mide 200 mm: lo que dejan las columnas fijas se reparte entre
    # las columnas de notas parciales (una por categoría, en cada cuatrimestre).
    ancho_parcial = max(5.0, (200 - 143.6) / (2 * max(len(categorias), 1)))

    return render(request, "calificaciones/planilla.html", {
        "cuat": cuat,
        "materia": materia,
        "curso": _texto_curso(materia.curso),
        "docente_nombre": _nombre_docente(materia),
        "turno": datos_planilla.turno if datos_planilla else "",
        "preceptor": datos_planilla.preceptor if datos_planilla else "",
        "puede_editar": puede_editar,
        "filas": filas,
        "categorias": categorias,
        "ancho_parcial": f"{ancho_parcial:.1f}",
        # Columnas de cada cuatrimestre: parciales (mínimo 1) + las fijas.
        "col_1c": max(len(categorias), 1) + 3,
        "col_2c": max(len(categorias), 1) + 4,
        "numeros_vacios": range(len(filas) + 1, 38),  # la hoja oficial tiene 37 renglones
        "clases": {1: _clases_dadas(materia, 1), 2: _clases_dadas(materia, 2)},
        "totales": _totales_planilla(filas),
        "ciclo_lectivo": timezone.now().year,
    })


def _filas_planilla(materia, categorias, cuat):
    """Una fila por alumno con todo lo que muestra la planilla."""
    notas = {1: {}, 2: {}}  # {cuat: {alumno_id: {categoria_id: valor}}}
    for n in NotaEvaluacion.objects.filter(materia=materia).order_by("id"):
        if n.cuatrimestre in notas:
            notas[n.cuatrimestre].setdefault(n.alumno_id, {})[n.categoria_id] = n.valor
    cierres = {
        (c.alumno_id, c.cuatrimestre): c
        for c in CierreCuatrimestre.objects.filter(materia=materia)
    }
    inasistencias = {
        (i.alumno_id, i.cuatrimestre): i.cantidad
        for i in InasistenciaMateria.objects.filter(materia=materia)
    }

    filas = []
    for nro, alumno in enumerate(_alumnos_del_curso(materia.curso), start=1):
        cierre1 = cierres.get((alumno.id, 1))
        cierre2 = cierres.get((alumno.id, 2))
        d1 = _datos_cuatrimestre(notas[1].get(alumno.id, {}), categorias, cierre1)
        d2 = _datos_cuatrimestre(notas[2].get(alumno.id, {}), categorias, cierre2)

        # Regla del 80 %: sin asistencia suficiente, nada queda aprobado.
        asistencia = _asistencia_materia(alumno.id, materia)
        asistencia_ok = asistencia is None or asistencia["suficiente"]
        if not asistencia_ok:
            d1["aprobada"] = d2["aprobada"] = False

        inas = {}
        for c in (1, 2):
            valor = inasistencias.get((alumno.id, c))
            if valor is None:
                valor = _inasistencias_materia_cuat(alumno.id, materia, c)
            inas[c] = _formato_ar(valor) or ""

        cierre_actual = cierres.get((alumno.id, cuat))  # el cuatrimestre que se edita
        final = _calificacion_final(d1, d2, cierre1, cierre2)

        filas.append({
            "nro": nro,
            "id": alumno.id,
            "nombre": f"{alumno.apellido}, {alumno.nombre}",
            "nombre_planilla": f"{alumno.apellido.upper()} {alumno.nombre}",
            "cursada": cierre_actual.cursada if cierre_actual else "C",
            "d1": d1,
            "d2": d2,
            "inas1": inas[1],
            "inas2": inas[2],
            "intensificacion": _intensificacion(cierre1),
            "dic": _num_limpio(cierre_actual.nota_diciembre) if cierre_actual and cierre_actual.nota_diciembre is not None else "",
            "feb": _num_limpio(cierre_actual.nota_febrero) if cierre_actual and cierre_actual.nota_febrero is not None else "",
            "final": final,
            "final_aprobada": bool(final) and Decimal(final) >= NOTA_APROBACION and asistencia_ok,
            "no_acredita": not asistencia_ok,
        })
    return filas


def _totales_planilla(filas):
    """Cuadro de totales del pie: 1°C, 2°C, total anual, diciembre y febrero."""
    def contar(condicion):
        return sum(1 for f in filas if condicion(f))

    def aprueba(nota_texto, fila):
        return Decimal(nota_texto) >= NOTA_APROBACION and not fila["no_acredita"]

    con_dic = [f for f in filas if f["dic"]]
    con_feb = [f for f in filas if f["feb"]]
    return {
        "estudiantes": [len(filas), len(filas), len(filas), len(con_dic), len(con_feb)],
        "aprobados": [
            contar(lambda f: f["d1"]["aprobada"]),
            contar(lambda f: f["d2"]["aprobada"]),
            contar(lambda f: f["final_aprobada"]),
            sum(1 for f in con_dic if aprueba(f["dic"], f)),
            sum(1 for f in con_feb if aprueba(f["feb"], f)),
        ],
        "desaprobados": [
            contar(lambda f: f["d1"]["tiene_calificacion"] and not f["d1"]["aprobada"]),
            contar(lambda f: f["d2"]["tiene_calificacion"] and not f["d2"]["aprobada"]),
            contar(lambda f: f["final"] and not f["final_aprobada"]),
            sum(1 for f in con_dic if not aprueba(f["dic"], f)),
            sum(1 for f in con_feb if not aprueba(f["feb"], f)),
        ],
        "sin_evaluar": [
            contar(lambda f: not f["d1"]["tiene_calificacion"]),
            contar(lambda f: not f["d2"]["tiene_calificacion"]),
            contar(lambda f: not f["final"]),
            0,
            0,
        ],
    }


def _guardar_planilla(request, materia, cuat):
    """Guarda lo editable de la planilla y, si se pidió, cierra el cuatrimestre."""
    cerrar = request.POST.get("accion") == "cerrar"

    # Encabezado: turno y preceptor/a.
    PlanillaDatos.objects.update_or_create(materia=materia, defaults={
        "turno": request.POST.get("turno", "").strip()[:50],
        "preceptor": request.POST.get("preceptor", "").strip()[:100],
    })

    categorias = _categorias(materia)
    for alumno in _alumnos_del_curso(materia.curso):
        cierre, _ = CierreCuatrimestre.objects.get_or_create(
            alumno=alumno, materia=materia, cuatrimestre=cuat,
        )
        cursada = request.POST.get(f"cursada_{alumno.id}", "C").strip().upper()
        cierre.cursada = cursada if cursada in ("C", "R") else "C"
        cierre.nota_diciembre = _nota_desde_texto(request.POST.get(f"dic_{alumno.id}"))
        cierre.nota_febrero = _nota_desde_texto(request.POST.get(f"feb_{alumno.id}"))

        if cerrar:
            # Al cerrar, la calificación calculada queda fija en el cierre.
            notas = {
                n.categoria_id: n.valor
                for n in NotaEvaluacion.objects.filter(alumno=alumno, materia=materia, cuatrimestre=cuat)
            }
            calif = _calificacion_entera(notas, categorias)
            if calif is not None:
                cierre.calificacion = calif
            cierre.cerrado = True
        cierre.save()

        # Inasistencias de los dos cuatrimestres (vacío = volver a las de Asistencia).
        for c in (1, 2):
            texto = request.POST.get(f"inas{c}_{alumno.id}")
            if texto is None:
                continue
            filtro = {"alumno": alumno, "materia": materia, "cuatrimestre": c}
            cantidad = _inasistencia_desde_texto(texto)
            if cantidad is not None:
                InasistenciaMateria.objects.update_or_create(**filtro, defaults={"cantidad": cantidad})
            elif texto.strip() == "":
                InasistenciaMateria.objects.filter(**filtro).delete()

    if cerrar:
        # Fecha de cierre del cuatrimestre (se muestra en el inicio del docente).
        BoletinConfig.objects.update_or_create(
            cuatrimestre=cuat, defaults={"publicado": True, "fecha_publicacion": timezone.now()},
        )
        messages.success(request, f"Cierre del {cuat}° cuatrimestre guardado.")
    else:
        messages.success(request, "Cambios guardados.")


# ─────────────────────────────────────────────
#  BOLETÍN (RITE)
# ─────────────────────────────────────────────

@rol_requerido("docente", "administrativo", "directivo")
def alumno_seleccionar(request):
    """Buscador de alumno para abrir su boletín."""
    alumnos = Alumno.objects.filter(activo=True).order_by("anio", "division", "apellido", "nombre")
    return render(request, "calificaciones/alumno_seleccionar.html", {
        "alumnos": alumnos,
        "boletin_publicado": _boletin_publicado(),
        "puede_ver": _puede_ver_boletin(request),
    })


def _alumno_a_mostrar(request):
    """El alumno ve SIEMPRE su propio boletín; los demás roles eligen con alumno_id."""
    perfil = getattr(request.user, "perfil", None)
    if perfil is not None and perfil.rol == "alumno":
        return perfil.alumno
    alumno_id = request.POST.get("alumno_id") or request.GET.get("alumno_id")
    if not alumno_id or not str(alumno_id).isdigit():
        return None
    return get_object_or_404(Alumno, id=alumno_id, activo=True)


def _datos_rite(alumno, usuario):
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
    perfil = getattr(usuario, "perfil", None)
    es_alumno = perfil is not None and perfil.rol == "alumno"
    firmas = []
    for tipo, nombre in ConfirmacionRite.TIPO_CHOICES:
        firmas.append({
            "tipo": tipo,
            "nombre": nombre,
            "c1": (1, tipo) in firmadas,
            "c2": (2, tipo) in firmadas,
            # [(1, firmada?), (2, firmada?)] para dibujar una celda por cuatrimestre.
            "estados": [(c, (c, tipo) in firmadas) for c in (1, 2)],
            # El alumno firma solo como estudiante; los demás, por el resto.
            "puede_firmar": (tipo == "estudiante") == es_alumno,
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
        "es_alumno": es_alumno,
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
    return render(request, "calificaciones/boletin.html", _datos_rite(alumno, request.user))


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

    es_alumno = _rol(request) == "alumno"
    if es_alumno and tipo != "estudiante":
        messages.error(request, "Solo podés firmar por vos.")
        return destino
    if not es_alumno and tipo == "estudiante":
        messages.error(request, "La firma del estudiante la registra el propio alumno.")
        return destino

    ConfirmacionRite.objects.update_or_create(
        alumno=alumno, cuatrimestre=int(cuat), tipo=tipo,
        defaults={"usuario": request.user.get_username()},
    )
    messages.success(request, "Firma registrada.")
    return destino
