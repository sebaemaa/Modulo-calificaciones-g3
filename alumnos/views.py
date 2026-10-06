import os
import json
from datetime import date
from decimal import Decimal
from functools import wraps
from urllib.parse import quote

from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache

from asistencia.models import ESTADO_CHOICES, RegistroAsistencia
from calificaciones.models import Calificacion, PERIODO_CHOICES
from docentes.models import Docente, Materia

from .models import (
    Alumno,
    Curso,
    ExpedienteDocumento,
    HistorialAcademicoAnual,
    HistorialBajaAlumno,
    HistorialPromocionAlumno,
    ObservacionAcademica,
    RegistroActividadAlumno,
    ResponsableAlumno,
    TutorAlumno,
)

ESTADO_ASISTENCIA_LABELS = dict(ESTADO_CHOICES)
PERIODO_LABELS = dict(PERIODO_CHOICES)


def _decimal_to_float(value):
    if value is None:
        return None
    return float(value)


def registrar_actividad(request, entidad, objeto_id, accion, descripcion, alumno=None):
    correo_electronico = ""
    if getattr(request, "user", None) and request.user.is_authenticated:
        correo_electronico = request.user.email or request.user.username or ""

    RegistroActividadAlumno.objects.create(
        alumno=alumno,
        correo_electronico=correo_electronico,
        entidad=entidad,
        objeto_id=str(objeto_id),
        accion=accion,
        descripcion=descripcion,
    )


def _evaluar_promocion(alumno):
    historial = obtener_historial_academico(alumno)
    resumen = historial.get("resumen", {})
    promedio = resumen.get("promedio_general")
    asistencia = resumen.get("asistencia_porcentaje")

    if not alumno.activo:
        return False, "Estado inactivo", {"promedio": promedio, "asistencia": asistencia}
    if alumno.anio >= 7:
        return False, "Curso finalizado", {"promedio": promedio, "asistencia": asistencia}
    if promedio is None:
        return False, "Sin calificaciones registradas", {"promedio": promedio, "asistencia": asistencia}
    if promedio < 6:
        return False, "Promedio insuficiente", {"promedio": promedio, "asistencia": asistencia}
    if asistencia is None:
        return False, "Sin asistencia registrada", {"promedio": promedio, "asistencia": asistencia}
    if asistencia < 75:
        return False, "Exceso de inasistencias", {"promedio": promedio, "asistencia": asistencia}

    return True, "Cumple requisitos", {"promedio": promedio, "asistencia": asistencia}


def _registrar_historial_anual(
    *,
    alumno,
    anio_lectivo,
    curso,
    division,
    estado_alumno,
    resultado_final,
    fecha_promocion=None,
    fecha_baja=None,
    observaciones="",
    estado_promocion=HistorialAcademicoAnual.EstadoPromocion.PROMOCIONADO,
    motivo_no_promocion="",
):
    historial, _ = HistorialAcademicoAnual.objects.update_or_create(
        alumno=alumno,
        anio_lectivo=anio_lectivo,
        defaults={
            "curso": curso,
            "division": division,
            "estado_alumno": estado_alumno,
            "resultado_final": resultado_final,
            "fecha_promocion": fecha_promocion,
            "fecha_baja": fecha_baja,
            "observaciones": observaciones,
            "estado_promocion": estado_promocion,
            "motivo_no_promocion": motivo_no_promocion,
        },
    )
    return historial


def _serializar_historial_anual(alumno):
    historial = []
    for row in alumno.historiales_academicos_anuales.all().order_by("-anio_lectivo", "-id"):
        historial.append(
            {
                "id": row.id,
                "anio_lectivo": row.anio_lectivo,
                "curso": row.curso,
                "division": row.division,
                "estado_alumno": row.estado_alumno,
                "resultado_final": row.resultado_final,
                "fecha_promocion": _fecha_iso(row.fecha_promocion),
                "fecha_baja": _fecha_iso(row.fecha_baja),
                "observaciones": row.observaciones,
                "estado_promocion": row.estado_promocion,
                "estado_promocion_label": row.get_estado_promocion_display(),
                "motivo_no_promocion": row.motivo_no_promocion,
            }
        )
    return historial


def obtener_historial_academico(alumno):
    calificaciones_qs = Calificacion.objects.filter(alumno=alumno).select_related("materia", "materia__docente").order_by("periodo", "materia__nombre")
    asistencias_qs = RegistroAsistencia.objects.filter(alumno=alumno).select_related("materia", "materia__docente").order_by("-fecha", "materia__nombre")
    observaciones_qs = ObservacionAcademica.objects.filter(alumno=alumno).order_by("-fecha", "-id")

    calificaciones_por_periodo = []
    for periodo_code, periodo_label in PERIODO_CHOICES:
        items = []
        notas = []
        for calificacion in calificaciones_qs.filter(periodo=periodo_code):
            nota = _decimal_to_float(calificacion.nota)
            if nota is not None:
                notas.append(nota)
            items.append(
                {
                    "id": calificacion.id,
                    "materia": calificacion.materia.nombre,
                    "docente": str(calificacion.materia.docente) if calificacion.materia.docente else "",
                    "nota": nota,
                }
            )
        calificaciones_por_periodo.append(
            {
                "periodo": periodo_code,
                "periodo_label": periodo_label,
                "promedio": round(sum(notas) / len(notas), 2) if notas else None,
                "cantidad": len(items),
                "items": items,
            }
        )

    asistencia_total = asistencias_qs.count()
    asistencia_por_estado = {estado: 0 for estado in ESTADO_ASISTENCIA_LABELS}
    for row in asistencias_qs.values("estado"):
        asistencia_por_estado[row["estado"]] = asistencia_por_estado.get(row["estado"], 0) + 1

    asistencias_items = [
        {
            "id": registro.id,
            "fecha": registro.fecha.strftime("%d/%m/%Y"),
            "materia": registro.materia.nombre,
            "docente": str(registro.materia.docente) if registro.materia.docente else "",
            "estado": registro.estado,
            "estado_label": ESTADO_ASISTENCIA_LABELS.get(registro.estado, registro.estado),
        }
        for registro in asistencias_qs[:30]
    ]

    observaciones_items = [
        {
            "id": observacion.id,
            "periodo": observacion.periodo,
            "periodo_label": PERIODO_LABELS.get(observacion.periodo, "General"),
            "conducta": observacion.conducta,
            "conducta_label": observacion.get_conducta_display(),
            "observacion": observacion.observacion,
            "fecha": observacion.fecha.strftime("%d/%m/%Y %H:%M"),
            "creado_por": observacion.creado_por.username if observacion.creado_por else "",
        }
        for observacion in observaciones_qs
    ]

    presentes = asistencia_por_estado.get("P", 0)
    ausentes = asistencia_por_estado.get("A", 0)
    tardanzas = asistencia_por_estado.get("T", 0)
    asistencia_porcentaje = round((presentes * 100 / asistencia_total), 2) if asistencia_total else None

    conducta_actual = observaciones_items[0]["conducta"] if observaciones_items else ""
    conducta_actual_label = observaciones_items[0]["conducta_label"] if observaciones_items else "Sin observaciones"

    promedio_general = []
    for periodo in calificaciones_por_periodo:
        if periodo["promedio"] is not None:
            promedio_general.append(periodo["promedio"])

    return {
        "resumen": {
            "promedio_general": round(sum(promedio_general) / len(promedio_general), 2) if promedio_general else None,
            "asistencia_total": asistencia_total,
            "asistencia_porcentaje": asistencia_porcentaje,
            "presentes": presentes,
            "ausentes": ausentes,
            "tardanzas": tardanzas,
            "conducta_actual": conducta_actual,
            "conducta_actual_label": conducta_actual_label,
            "observaciones_total": len(observaciones_items),
        },
        "calificaciones_por_periodo": calificaciones_por_periodo,
        "asistencia": {
            "total": asistencia_total,
            "por_estado": asistencia_por_estado,
            "items": asistencias_items,
        },
        "observaciones": observaciones_items,
        "calificaciones_total": sum(periodo["cantidad"] for periodo in calificaciones_por_periodo),
    }



def _is_admin_user(request):
    return bool(
        request.user
        and request.user.is_authenticated
        and (request.user.is_superuser or request.user.is_staff)
    )


def _is_preceptor(request):
    if not request.user or not request.user.is_authenticated:
        return False
    username = (request.user.username or "").lower()
    group_names = {g.name.lower() for g in request.user.groups.all()}
    return bool(
        "preceptor" in username
        or "preceptor" in group_names
    )


def _is_directivo(request):
    if not request.user or not request.user.is_authenticated:
        return False
    if request.user.is_superuser:
        return True
    username = (request.user.username or "").lower()
    group_names = {g.name.lower() for g in request.user.groups.all()}
    return "directivo" in username or "directivo" in group_names


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            next_url = request.get_full_path()
            return redirect(f"{reverse('login')}?next={quote(next_url, safe='/')}")
        if not _is_admin_user(request):
            return HttpResponseForbidden(
                "Acceso denegado: solo personal administrador."
            )
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def _guardar_documentacion(alumno, archivos):
    if not archivos:
        return

    base_dir = os.path.join("alumnos", "documentacion", str(alumno.pk))
    rutas_guardadas = []

    for archivo in archivos:
        nombre = archivo.name
        destino = os.path.join(base_dir, nombre)

        contador = 1
        stem, ext = os.path.splitext(nombre)
        while default_storage.exists(destino):
            destino = os.path.join(base_dir, f"{stem}_{contador}{ext}")
            contador += 1

        rutas_guardadas.append(default_storage.save(destino, archivo))

    if rutas_guardadas:
        alumno.documentacion = rutas_guardadas[0]
        alumno.save(update_fields=["documentacion"])


def _obtener_archivos_documentacion(request):
    archivos = []

    # Carga adicional múltiple (compatibilidad con versión previa).
    archivos.extend(request.FILES.getlist("documentacion"))

    # Carga por apartados requeridos. Se agrega prefijo para que el sistema
    # clasifique correctamente el archivo dentro de la documentación requerida.
    prefijos_por_campo = {
        "documentacion_identidad": "documento",
        "documentacion_partida": "partida",
        "documentacion_vacunas": "vacunas",
        "documentacion_constancia": "constancia",
    }

    for field_name, prefijo in prefijos_por_campo.items():
        archivo = request.FILES.get(field_name)
        if archivo:
            original_name = os.path.basename(getattr(archivo, "name", "archivo"))
            archivo.name = f"{prefijo}_{original_name}"
            archivos.append(archivo)

    return archivos


def _guardar_certificado_baja_pdf(alumno, archivo):
    if not archivo or not getattr(archivo, "name", ""):
        return ""

    _, ext = os.path.splitext(archivo.name)
    if ext.lower() != ".pdf":
        return ""

    base_dir = os.path.join("alumnos", "bajas", str(alumno.pk))
    destino = os.path.join(base_dir, "certificado_baja.pdf")

    contador = 1
    while default_storage.exists(destino):
        destino = os.path.join(base_dir, f"certificado_baja_{contador}.pdf")
        contador += 1

    return default_storage.save(destino, archivo)


def _guardar_certificado_responsable_pdf(alumno, archivo, nombre_base):
    if not archivo or not getattr(archivo, "name", ""):
        return ""

    _, ext = os.path.splitext(archivo.name)
    if ext.lower() != ".pdf":
        return ""

    base_dir = os.path.join("alumnos", "responsables_certificados", str(alumno.pk))
    filename = f"{nombre_base}.pdf"
    destino = os.path.join(base_dir, filename)

    contador = 1
    while default_storage.exists(destino):
        destino = os.path.join(base_dir, f"{nombre_base}_{contador}.pdf")
        contador += 1

    return default_storage.save(destino, archivo)


def _fecha_iso(value):
    return value.strftime("%Y-%m-%d") if value else ""


def _estado_documento_label(estado):
    return dict(ExpedienteDocumento.EstadoDocumento.choices).get(estado, estado)


def _snapshot_alumno(alumno):
    responsables = []
    for r in alumno.responsables.all().order_by("n_orden", "apellido", "nombre"):
        responsables.append(
            {
                "tipo_responsable": r.tipo_responsable,
                "nombre": r.nombre,
                "apellido": r.apellido,
                "dni": r.dni,
                "fecha_nacimiento": r.fecha_nacimiento.isoformat() if r.fecha_nacimiento else "",
                "telefono": r.telefono,
                "telefono_alternativo": r.telefono_alternativo,
                "correo_electronico": r.correo_electronico,
                "puede_retirar": r.puede_retirar,
                "perimetral": r.perimetral,
                "perimetral_motivo": r.perimetral_motivo,
            }
        )

    return {
        "alumno_id": alumno.id,
        "nombre": alumno.nombre,
        "apellido": alumno.apellido,
        "tipo_identificacion": alumno.tipo_identificacion,
        "identificacion": alumno.dni,
        "fecha_nacimiento": alumno.fecha_nacimiento.isoformat() if alumno.fecha_nacimiento else "",
        "domicilio": alumno.domicilio,
        "telefono_contacto": alumno.telefono_contacto,
        "anio": alumno.anio,
        "division": alumno.division,
        "activo": alumno.activo,
        "estado_promocion": alumno.estado_promocion,
        "motivo_no_promocion": alumno.motivo_no_promocion,
        "responsables": responsables,
    }


def _post_tiene_payload_responsables(request):
    # Solo considerar campos exclusivos del bloque de responsables.
    # Evita colisión con campos del alumno (dni, fecha_nacimiento, domicilio, etc.).
    claves_responsables = {
        "responsable_id[]",
        "tipo_responsable[]",
        "nombres[]",
        "apellidos[]",
        "dni[]",
        "fecha_nacimiento[]",
        "parentesco[]",
        "telefonos[]",
        "telefono_alternativo[]",
        "correo_electronico[]",
        "ocupacion[]",
        "domicilio[]",
        "localidad[]",
        "provincia[]",
        "codigo_postal[]",
        "n_orden[]",
        "puede_retirar_ui[]",
        "puede_retirar_flags[]",
        "perimetral_tiene[]",
        "perimetral_motivo[]",
        "anotaciones_particulares[]",
    }
    return any(k in request.POST for k in claves_responsables)


def _validar_responsables_post(request):
    if not _post_tiene_payload_responsables(request):
        return None

    def _get_list(*names):
        for name in names:
            valores = request.POST.getlist(name)
            if valores:
                return valores
        return request.POST.getlist(names[0]) if names else []

    tipo_responsable = _get_list("tipo_responsable[]", "tipo_responsable")
    nombres = _get_list("nombres[]", "nombres")
    apellidos = _get_list("apellidos[]", "apellidos")
    dni_list = _get_list("dni[]", "dni")
    fecha_nacimiento_list = _get_list("fecha_nacimiento[]", "fecha_nacimiento")

    n = max(len(tipo_responsable), len(nombres), len(apellidos), len(dni_list), len(fecha_nacimiento_list))

    def _pad(lst, n_):
        return (lst or []) + [""] * max(0, n_ - len(lst or []))

    tipo_responsable = _pad(tipo_responsable, n)
    nombres = _pad(nombres, n)
    apellidos = _pad(apellidos, n)
    dni_list = _pad(dni_list, n)
    fecha_nacimiento_list = _pad(fecha_nacimiento_list, n)

    for i in range(n):
        tipo = (tipo_responsable[i] or "").strip()
        nombre = (nombres[i] or "").strip()
        apellido = (apellidos[i] or "").strip()
        dni = (dni_list[i] or "").strip()
        fecha_raw = (fecha_nacimiento_list[i] or "").strip()

        if not any([tipo, nombre, apellido, dni, fecha_raw]):
            continue

        if not nombre or not apellido or not dni or not fecha_raw:
                return f"Completá nombre, apellido, DNI y fecha de nacimiento del responsable/tutor en el bloque {i + 1}."

    return None


@admin_required
def _parse_responsables_post(request, alumno, *, delete_missing=False):
    """Guarda (crea/actualiza/elimina) responsables desde POST.

    Convención de inputs (por bloque):
    - responsable_id[] (opcional en alta; requerido en edición)
    - tipo_responsable[]
    - nombres/apellidos
    - dni, fecha_nacimiento, parentesco
    - telefono, telefono_alternativo, correo_electronico
    - domicilio, localidad, provincia, codigo_postal
    - ocupacion, lugar_trabajo
    - observaciones
    - n_orden
    """

    def _get_list(*names):
        for name in names:
            v = request.POST.getlist(name)
            if v is not None and len(v) > 0:
                return v
        return request.POST.getlist(names[0]) if names else []

    tipo_responsable = _get_list("tipo_responsable[]", "tipo_responsable")
    nombres = _get_list("nombres[]", "nombres")
    apellidos = _get_list("apellidos[]", "apellidos")

    dni_list = _get_list("dni[]", "dni")
    fecha_nacimiento_list = _get_list("fecha_nacimiento[]", "fecha_nacimiento")
    parentesco_list = _get_list("parentescos[]", "parentesco[]", "parentesco")

    telefono_list = _get_list("telefonos[]", "telefono[]", "telefono")
    telefono_alt_list = _get_list("telefono_alternativo[]", "telefonos_alternativos[]", "telefono_alternativo")
    correo_list = _get_list("correo_electronico[]", "correos[]", "correo")

    domicilio_list = _get_list("domicilios[]", "domicilio[]", "domicilio")
    localidad_list = _get_list("localidades[]", "localidad[]", "localidad")
    provincia_list = _get_list("provincias[]", "provincia[]", "provincia")
    cp_list = _get_list("codigo_postal[]", "cp[]", "codigo_postal")

    ocupacion_list = _get_list("ocupaciones[]", "ocupacion[]", "ocupacion")
    lugar_trabajo_list = _get_list("lugares_trabajo[]", "lugar_trabajo[]", "lugar_trabajo")

    nacionalidad_list = _get_list("nacionalidad[]", "nacionalidades[]")
    profesion_list = _get_list("profesion[]", "profesiones[]")

    cert_antivariolico_list = _get_list("cert_antivariolico[]", "cert_antivariolicos[]")
    cert_antidifterico_list = _get_list("cert_antidifterico[]", "cert_antidiftericos[]")
    cert_antipolio_list = _get_list("cert_antipolio[]", "cert_antipolios[]")
    cert_buco_dental_list = _get_list("cert_buco_dental[]", "cert_buco_dentales[]")

    perimetral_list = _get_list("perimetral[]", "perimetrales[]")
    perimetral_tiene_list = _get_list("perimetral_tiene[]", "perimetral_tiene")
    perimetral_motivo_list = _get_list("perimetral_motivo[]", "perimetral_motivo")
    puede_retirar_list = _get_list("puede_retirar[]", "puede_retirar_flags[]")

    anotaciones_particulares_list = _get_list("anotaciones_particulares[]", "anotaciones_particulares")

    observaciones_list = _get_list("observaciones[]", "observaciones")

    n_orden_list = _get_list("n_orden[]", "n_orden")

    responsable_ids = request.POST.getlist("responsable_id[]") or request.POST.getlist("responsable_id")

    n = max(
        len(tipo_responsable),
        len(nombres),
        len(apellidos),
        len(dni_list),
        len(fecha_nacimiento_list),
    )

    def _pad(lst, n_):
        return (lst or []) + [""] * max(0, n_ - len(lst or []))

    tipo_responsable = _pad(tipo_responsable, n)
    nombres = _pad(nombres, n)
    apellidos = _pad(apellidos, n)
    dni_list = _pad(dni_list, n)
    fecha_nacimiento_list = _pad(fecha_nacimiento_list, n)
    parentesco_list = _pad(parentesco_list, n)

    telefono_list = _pad(telefono_list, n)
    telefono_alt_list = _pad(telefono_alt_list, n)
    correo_list = _pad(correo_list, n)

    domicilio_list = _pad(domicilio_list, n)
    localidad_list = _pad(localidad_list, n)
    provincia_list = _pad(provincia_list, n)
    cp_list = _pad(cp_list, n)

    ocupacion_list = _pad(ocupacion_list, n)
    lugar_trabajo_list = _pad(lugar_trabajo_list, n)

    observaciones_list = _pad(observaciones_list, n)
    n_orden_list = _pad(n_orden_list, n)

    nacionalidad_list = _pad(nacionalidad_list, n)
    profesion_list = _pad(profesion_list, n)

    cert_antivariolico_list = _pad(cert_antivariolico_list, n)
    cert_antidifterico_list = _pad(cert_antidifterico_list, n)
    cert_antipolio_list = _pad(cert_antipolio_list, n)
    cert_buco_dental_list = _pad(cert_buco_dental_list, n)

    perimetral_list = _pad(perimetral_list, n)
    perimetral_tiene_list = _pad(perimetral_tiene_list, n)
    perimetral_motivo_list = _pad(perimetral_motivo_list, n)
    puede_retirar_list = _pad(puede_retirar_list, n)
    anotaciones_particulares_list = _pad(anotaciones_particulares_list, n)

    ids_by_index = [str(x) for x in responsable_ids] if responsable_ids else []

    existentes = {}
    if delete_missing and ids_by_index:
        qs = ResponsableAlumno.objects.filter(alumno=alumno, id__in=ids_by_index)
        existentes = {str(x.id): x for x in qs}

    ids_seen = set()

    for i in range(n):
        tipo = (tipo_responsable[i] or "").strip()
        nombre = (nombres[i] or "").strip()
        apellido = (apellidos[i] or "").strip()
        dni = (dni_list[i] or "").strip()
        fecha_raw = (fecha_nacimiento_list[i] or "").strip()

        if not tipo and not nombre and not apellido and not dni:
            continue

        if not fecha_raw:
            # Evita IntegrityError en DateField de responsables nuevos o editados.
            continue

        responsable_id = ids_by_index[i] if i < len(ids_by_index) else ""

        if delete_missing and responsable_id and responsable_id in existentes:
            resp = existentes[responsable_id]
        else:
            resp = ResponsableAlumno(alumno=alumno)
            resp.n_orden = i + 1

        resp.tipo_responsable = tipo or ResponsableAlumno.TipoResponsable.OTRO
        resp.nombre = nombre
        resp.apellido = apellido
        resp.dni = dni
        resp.fecha_nacimiento = fecha_raw

        resp.parentesco = (parentesco_list[i] or "").strip()
        resp.telefono = (telefono_list[i] or "").strip()
        resp.telefono_alternativo = (telefono_alt_list[i] or "").strip()
        resp.correo_electronico = (correo_list[i] or "").strip()

        resp.domicilio = (domicilio_list[i] or "").strip()
        resp.localidad = (localidad_list[i] or "").strip()
        resp.provincia = (provincia_list[i] or "").strip()
        resp.codigo_postal = (cp_list[i] or "").strip()

        resp.ocupacion = (ocupacion_list[i] or "").strip()
        resp.lugar_trabajo = (lugar_trabajo_list[i] or "").strip()

        resp.nacionalidad = (nacionalidad_list[i] or "").strip()
        resp.profesion = (profesion_list[i] or "").strip()

        resp.certificado_antivariolico = (cert_antivariolico_list[i] or "").strip()
        resp.certificado_antidifterico = (cert_antidifterico_list[i] or "").strip()
        resp.certificado_antipolio = (cert_antipolio_list[i] or "").strip()
        resp.certificado_buco_dental = (cert_buco_dental_list[i] or "").strip()

        orden_raw = (n_orden_list[i] or "").strip()
        try:
            orden_for_file = int(orden_raw) if orden_raw else (i + 1)
        except ValueError:
            orden_for_file = i + 1

        cert_antivariolico_file = request.FILES.get(f"cert_antivariolico_file_{orden_for_file}")
        cert_antidifterico_file = request.FILES.get(f"cert_antidifterico_file_{orden_for_file}")
        cert_antipolio_file = request.FILES.get(f"cert_antipolio_file_{orden_for_file}")
        cert_buco_dental_file = request.FILES.get(f"cert_buco_dental_file_{orden_for_file}")
        perimetral_file = request.FILES.get(f"perimetral_file_{orden_for_file}")

        if cert_antivariolico_file:
            path = _guardar_certificado_responsable_pdf(
                alumno,
                cert_antivariolico_file,
                f"responsable_{orden_for_file}_antivariolico",
            )
            if path:
                resp.certificado_antivariolico = path

        if cert_antidifterico_file:
            path = _guardar_certificado_responsable_pdf(
                alumno,
                cert_antidifterico_file,
                f"responsable_{orden_for_file}_antidifterico",
            )
            if path:
                resp.certificado_antidifterico = path

        if cert_antipolio_file:
            path = _guardar_certificado_responsable_pdf(
                alumno,
                cert_antipolio_file,
                f"responsable_{orden_for_file}_antipolio",
            )
            if path:
                resp.certificado_antipolio = path

        if cert_buco_dental_file:
            path = _guardar_certificado_responsable_pdf(
                alumno,
                cert_buco_dental_file,
                f"responsable_{orden_for_file}_buco_dental",
            )
            if path:
                resp.certificado_buco_dental = path

        tiene_perimetral_raw = (perimetral_tiene_list[i] or "").strip()
        tiene_perimetral = tiene_perimetral_raw in {"1", "true", "True", "on", "yes", "SI", "si"}
        perimetral_motivo = (perimetral_motivo_list[i] or "").strip()

        if tiene_perimetral:
            resp.perimetral = (perimetral_list[i] or resp.perimetral or "").strip()
            resp.perimetral_motivo = perimetral_motivo
            if perimetral_file:
                path = _guardar_certificado_responsable_pdf(
                    alumno,
                    perimetral_file,
                    f"responsable_{orden_for_file}_perimetral",
                )
                if path:
                    resp.perimetral = path
        else:
            resp.perimetral = ""
            resp.perimetral_motivo = ""

        puede_retirar_raw = (puede_retirar_list[i] or "").strip()
        resp.puede_retirar = puede_retirar_raw in {"1", "true", "True", "on", "yes", "SI", "si"}

        resp.anotaciones_particulares = (anotaciones_particulares_list[i] or "").strip()
        resp.observaciones = (observaciones_list[i] or "").strip()

        try:
            resp.n_orden = int(orden_raw) if orden_raw else (i + 1)
        except ValueError:
            resp.n_orden = i + 1
        resp.save()

        ids_seen.add(str(resp.id))

    if delete_missing:
        ResponsableAlumno.objects.filter(alumno=alumno).exclude(id__in=ids_seen).delete()


@never_cache
@admin_required
def index(request):
    error = None
    warning = None

    if request.method == "POST":
        try:
            warning = _validar_responsables_post(request)

            with transaction.atomic():
                alumno = Alumno.objects.create(
                    nombre=request.POST["nombre"],
                    apellido=request.POST["apellido"],
                    dni=request.POST["dni"],
                    tipo_identificacion=request.POST.get("tipo_identificacion", Alumno.TipoIdentificacion.DOCUMENTO),
                    fecha_nacimiento=request.POST["fecha_nacimiento"],
                    domicilio=request.POST.get("domicilio", ""),
                    telefono_contacto=request.POST.get("telefono_contacto", ""),
                    anio=request.POST["anio"],
                    division=request.POST["division"],
                    activo=True,
                )
                _guardar_documentacion(alumno, _obtener_archivos_documentacion(request))
                registrar_actividad(
                    request,
                    "Alumno",
                    alumno.id,
                    "creado",
                    f"Alumno creado: {alumno.apellido}, {alumno.nombre}",
                    alumno=alumno,
                )

                if _post_tiene_payload_responsables(request):
                    _parse_responsables_post(request, alumno, delete_missing=False)

            response = redirect("alumnos:index")
            if warning:
                response["Location"] = f"{reverse('alumnos:index')}?warning={quote(warning, safe='')}"
            return response

        except IntegrityError:
            error = "Ya existe un alumno con ese DNI."


    busqueda = request.GET.get("buscar", "")
    anio = request.GET.get("anio", "")
    division = request.GET.get("division", "")

    alumnos_base = Alumno.objects.all().order_by("apellido", "nombre")
    alumnos = alumnos_base.filter(activo=True)
    warning = warning or (request.GET.get("warning") or "").strip()

    if busqueda:
        alumnos = alumnos.filter(
            Q(nombre__icontains=busqueda)
            | Q(apellido__icontains=busqueda)
            | Q(dni__icontains=busqueda)
            | Q(tipo_identificacion__icontains=busqueda)
        )

    if anio:
        alumnos = alumnos.filter(anio=anio)

    if division:
        alumnos = alumnos.filter(division=division)

    return render(
        request,
        "alumnos/index.html",
        {
            "alumnos": alumnos,
            "busqueda": busqueda,
            "anio_seleccionado": anio,
            "division_seleccionada": division,
            "total_alumnos": alumnos_base.count(),
            "activos": alumnos_base.filter(activo=True).count(),
            "inactivos": alumnos_base.filter(activo=False).count(),
            "can_edit_historial": _is_directivo(request),
            "can_manage_promo_baja": not _is_preceptor(request),
            "error": error,
            "warning": warning,
        },
    )

@never_cache
@admin_required
def dar_baja(request, id):
    if _is_preceptor(request):
        return HttpResponseForbidden("Acceso denegado: preceptor no puede dar de baja alumnos.")

    alumno = get_object_or_404(Alumno, id=id)

    if request.method == "POST":
        motivo_baja = (request.POST.get("motivo_baja") or "").strip()
        fecha_baja_raw = (request.POST.get("fecha_baja") or "").strip()
        certificado_baja_file = request.FILES.get("certificado_baja_file")

        snapshot = _snapshot_alumno(alumno)

        alumno.activo = False
        alumno.motivo_baja = motivo_baja
        alumno.fecha_baja = fecha_baja_raw or date.today().isoformat()
        if not alumno.motivo_no_promocion:
            alumno.motivo_no_promocion = "Baja del alumno"
        alumno.estado_promocion = Alumno.EstadoPromocion.NO_PROMOCIONADO

        if certificado_baja_file:
            path = _guardar_certificado_baja_pdf(alumno, certificado_baja_file)
            if path:
                alumno.certificado_baja = path

        alumno.save(
            update_fields=[
                "activo",
                "motivo_baja",
                "fecha_baja",
                "certificado_baja",
                "estado_promocion",
                "motivo_no_promocion",
            ]
        )
        registrar_actividad(
            request,
            "Alumno",
            alumno.id,
            "baja",
            f"Baja registrada para {alumno.apellido}, {alumno.nombre}",
            alumno=alumno,
        )

        try:
            anio_baja = int((alumno.fecha_baja or date.today()).year)
        except Exception:
            anio_baja = date.today().year

        HistorialBajaAlumno.objects.create(
            alumno=alumno,
            anio_baja=anio_baja,
            fecha_baja=alumno.fecha_baja or date.today(),
            motivo_baja=alumno.motivo_baja,
            certificado_baja=alumno.certificado_baja,
            snapshot=snapshot,
        )

        _registrar_historial_anual(
            alumno=alumno,
            anio_lectivo=anio_baja,
            curso=alumno.anio,
            division=alumno.division,
            estado_alumno="Inactivo",
            resultado_final="Baja",
            fecha_baja=alumno.fecha_baja,
            observaciones=alumno.motivo_baja,
            estado_promocion=HistorialAcademicoAnual.EstadoPromocion.NO_PROMOCIONADO,
            motivo_no_promocion=alumno.motivo_no_promocion or "Baja del alumno",
        )

        return redirect("alumnos:index")

    return redirect("alumnos:index")


@never_cache
@admin_required
def editar(request, id):
    alumno = get_object_or_404(Alumno, id=id)

    if request.method == "POST":
        try:
            alumno.nombre = request.POST["nombre"]
            alumno.apellido = request.POST["apellido"]
            alumno.dni = request.POST["dni"]
            alumno.tipo_identificacion = request.POST.get("tipo_identificacion", Alumno.TipoIdentificacion.DOCUMENTO)

            fecha = request.POST.get("fecha_nacimiento", "").strip()
            if fecha:
                alumno.fecha_nacimiento = fecha

            alumno.domicilio = request.POST.get("domicilio", "")
            alumno.telefono_contacto = request.POST.get("telefono_contacto", "")
            alumno.anio = request.POST["anio"]
            alumno.division = request.POST["division"]
            alumno.activo = request.POST.get("activo") == "1"

            archivos = _obtener_archivos_documentacion(request)
            if archivos:
                _guardar_documentacion(alumno, archivos)

            # Guardar responsables (sincronización completa) solo si llegaron campos de contacto.
            if _post_tiene_payload_responsables(request):
                _parse_responsables_post(request, alumno, delete_missing=True)

            alumno.save()
            registrar_actividad(
                request,
                "Alumno",
                alumno.id,
                "editado",
                f"Alumno actualizado: {alumno.apellido}, {alumno.nombre}",
                alumno=alumno,
            )
        except IntegrityError:
            pass
        except Exception:
            pass

    return redirect("alumnos:index")


@never_cache
@admin_required
def inactivos(request):
    busqueda = (request.GET.get("buscar") or "").strip()
    anio = (request.GET.get("anio") or "").strip()
    fecha_baja = (request.GET.get("fecha_baja") or "").strip()

    alumnos = Alumno.objects.filter(activo=False).order_by("-fecha_baja", "apellido", "nombre")

    if busqueda:
        alumnos = alumnos.filter(
            Q(nombre__icontains=busqueda)
            | Q(apellido__icontains=busqueda)
            | Q(dni__icontains=busqueda)
            | Q(division__icontains=busqueda)
            | Q(motivo_baja__icontains=busqueda)
        )

    if anio:
        alumnos = alumnos.filter(anio=anio)

    if fecha_baja:
        alumnos = alumnos.filter(fecha_baja=fecha_baja)

    for alumno in alumnos:
        historial_row = (
            alumno.historiales_academicos_anuales.filter(estado_alumno="Inactivo")
            .order_by("-anio_lectivo", "-id")
            .first()
        )
        alumno.observaciones_inactividad = historial_row.observaciones if historial_row else ""

    return render(
        request,
        "alumnos/inactivos.html",
        {
            "alumnos": alumnos,
            "busqueda": busqueda,
            "anio_seleccionado": anio,
            "fecha_baja_seleccionada": fecha_baja,
        },
    )


@never_cache
@admin_required
def promocion_curso_resumen(request):
    if _is_preceptor(request):
        return JsonResponse(
            {"ok": False, "message": "Acceso denegado: preceptor no puede promocionar alumnos."},
            status=403,
        )

    anio_raw = (request.GET.get("anio") or "").strip()
    division = (request.GET.get("division") or "").strip()

    if not anio_raw or not division:
        return JsonResponse({"ok": False, "message": "Debe seleccionar año y división."}, status=400)

    try:
        anio = int(anio_raw)
    except ValueError:
        return JsonResponse({"ok": False, "message": "Año inválido."}, status=400)

    alumnos = Alumno.objects.filter(anio=anio, division=division).order_by("apellido", "nombre")
    items = []

    for alumno in alumnos:
        puede, motivo, metricas = _evaluar_promocion(alumno)
        items.append(
            {
                "id": alumno.id,
                "nombre": alumno.nombre,
                "apellido": alumno.apellido,
                "dni": alumno.dni,
                "curso": alumno.anio,
                "division": alumno.division,
                "activo": alumno.activo,
                "estado": "Activo" if alumno.activo else "Inactivo",
                "resultado_evaluacion": {
                    "promedio": metricas.get("promedio"),
                    "asistencia": metricas.get("asistencia"),
                },
                "puede_promocionar": puede,
                "motivo": motivo,
            }
        )

    return JsonResponse({"ok": True, "items": items, "anio": anio, "division": division})


@never_cache
@admin_required
def confirmar_promocion_curso(request):
    if request.method != "POST":
        return redirect("alumnos:index")

    if _is_preceptor(request):
        return JsonResponse(
            {"ok": False, "message": "Acceso denegado: preceptor no puede promocionar alumnos."},
            status=403,
        )

    payload = {}
    if "application/json" in (request.content_type or ""):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            return JsonResponse({"ok": False, "message": "Payload inválido."}, status=400)

    anio_raw = str((payload.get("anio") if payload else request.POST.get("anio")) or "").strip()
    division = str((payload.get("division") if payload else request.POST.get("division")) or "").strip()

    try:
        anio = int(anio_raw)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "message": "Año inválido."}, status=400)

    decisiones_raw = payload.get("decisiones") if isinstance(payload, dict) else None
    decisiones_map = {}
    if isinstance(decisiones_raw, list):
        for d in decisiones_raw:
            try:
                alumno_id = int(d.get("alumno_id"))
            except (TypeError, ValueError):
                continue
            decisiones_map[alumno_id] = {
                "promover": bool(d.get("promover")),
                "motivo_no_promocion": (d.get("motivo_no_promocion") or "").strip(),
                "destino_mode": (d.get("destino_mode") or "misma").strip(),
                "destino_division": (d.get("destino_division") or "").strip(),
            }

    alumnos = Alumno.objects.filter(anio=anio, division=division).order_by("apellido", "nombre")
    hoy = date.today()
    promovidos = 0
    no_promovidos = 0
    detalle_no_promovidos = []
    faltantes = []

    if decisiones_map:
        for alumno in alumnos:
            decision = decisiones_map.get(alumno.id, {"promover": False, "motivo_no_promocion": ""})
            if not decision["promover"] and not decision["motivo_no_promocion"]:
                faltantes.append(f"{alumno.apellido}, {alumno.nombre}")

    if faltantes:
        return JsonResponse(
            {
                "ok": False,
                "message": "Debés registrar motivo para cada alumno no promocionado.",
                "faltantes": faltantes,
            },
            status=400,
        )

    for alumno in alumnos:
        puede, motivo, metricas = _evaluar_promocion(alumno)
        curso_origen = alumno.anio
        division_origen = alumno.division

        decision = decisiones_map.get(alumno.id) if decisiones_map else None
        promover = decision["promover"] if decision is not None else (puede and alumno.anio < 7)
        motivo_manual = (decision["motivo_no_promocion"] if decision is not None else "").strip()
        destino_mode = (decision.get("destino_mode") if decision is not None else "misma") or "misma"
        destino_division = (decision.get("destino_division") if decision is not None else "") or ""

        if promover and alumno.activo and alumno.anio < 7:
            alumno.anio = alumno.anio + 1
            if destino_mode == "cambiar" and destino_division in {"A", "B", "C", "D"}:
                alumno.division = destino_division
            alumno.estado_promocion = Alumno.EstadoPromocion.PROMOCIONADO
            alumno.motivo_no_promocion = ""
            alumno.save(update_fields=["anio", "division", "estado_promocion", "motivo_no_promocion"])

            HistorialPromocionAlumno.objects.create(
                alumno=alumno,
                ciclo_lectivo=hoy.year,
                fecha_promocion=hoy,
                anio_origen=curso_origen,
                anio_destino=alumno.anio,
                snapshot=_snapshot_alumno(alumno),
            )

            _registrar_historial_anual(
                alumno=alumno,
                anio_lectivo=hoy.year,
                curso=curso_origen,
                division=division_origen,
                estado_alumno="Activo",
                resultado_final="Promociona",
                fecha_promocion=hoy,
                observaciones=f"Promedio: {metricas.get('promedio')} | Asistencia: {metricas.get('asistencia')}%",
                estado_promocion=HistorialAcademicoAnual.EstadoPromocion.PROMOCIONADO,
            )
            promovidos += 1
            registrar_actividad(
                request,
                "Alumno",
                alumno.id,
                "promocion_curso",
                f"Promoción por curso: {curso_origen}{division_origen} a {alumno.anio}{alumno.division}",
                alumno=alumno,
            )
        else:
            motivo_final = motivo_manual or motivo or "No promocionado"
            alumno.estado_promocion = Alumno.EstadoPromocion.NO_PROMOCIONADO
            alumno.motivo_no_promocion = motivo_final
            alumno.save(update_fields=["estado_promocion", "motivo_no_promocion"])
            _registrar_historial_anual(
                alumno=alumno,
                anio_lectivo=hoy.year,
                curso=curso_origen,
                division=alumno.division,
                estado_alumno="Activo" if alumno.activo else "Inactivo",
                resultado_final="No promociona",
                observaciones=f"Promedio: {metricas.get('promedio')} | Asistencia: {metricas.get('asistencia')}%",
                estado_promocion=HistorialAcademicoAnual.EstadoPromocion.NO_PROMOCIONADO,
                motivo_no_promocion=motivo_final,
            )
            no_promovidos += 1
            detalle_no_promovidos.append(
                {
                    "alumno_id": alumno.id,
                    "alumno": f"{alumno.apellido}, {alumno.nombre}",
                    "motivo": motivo_final,
                }
            )
            registrar_actividad(
                request,
                "Alumno",
                alumno.id,
                "no_promocionado",
                f"No promociona: {motivo_final}",
                alumno=alumno,
            )

    return JsonResponse(
        {
            "ok": True,
            "promovidos": promovidos,
            "no_promovidos": no_promovidos,
            "anio": anio,
            "division": division,
            "detalle_no_promovidos": detalle_no_promovidos,
        }
    )



@never_cache
@admin_required
def reporte(request):
    anio = request.GET.get("anio", "")
    division = request.GET.get("division", "")
    estado = request.GET.get("estado", "ambos")

    alumnos = Alumno.objects.all().order_by("apellido", "nombre")

    if anio:
        alumnos = alumnos.filter(anio=anio)
    if division:
        alumnos = alumnos.filter(division=division)
    if estado == "activos":
        alumnos = alumnos.filter(activo=True)
    elif estado == "inactivos":
        alumnos = alumnos.filter(activo=False)

    activos_qs = alumnos.filter(activo=True)
    inactivos_qs = alumnos.filter(activo=False).order_by("-fecha_baja", "apellido", "nombre")

    return render(
        request,
        "alumnos/reporte.html",
        {
            "activos_lista": activos_qs,
            "inactivos_lista": inactivos_qs,
            "total": alumnos.count(),
            "activos": activos_qs.count(),
            "inactivos": inactivos_qs.count(),
            "anio_seleccionado": anio,
            "division_seleccionada": division,
            "estado_seleccionado": estado,
        },
    )


@never_cache
@admin_required
def ver_documento(request, alumno_id, nombre):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    ruta = os.path.join("alumnos", "documentacion", str(alumno.pk), nombre)

    if not default_storage.exists(ruta):
        raise Http404("No se encontró el archivo solicitado.")

    archivo = default_storage.open(ruta, "rb")
    response = FileResponse(archivo)
    response["Content-Disposition"] = f'inline; filename="{nombre}"'
    return response


@never_cache
@admin_required
def ver_certificado_baja(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    ruta = (alumno.certificado_baja or "").strip()

    if not ruta or not default_storage.exists(ruta):
        raise Http404("No se encontró el certificado de baja.")

    archivo = default_storage.open(ruta, "rb")
    response = FileResponse(archivo)
    response["Content-Disposition"] = 'inline; filename="certificado_baja.pdf"'
    return response


@never_cache
@admin_required
def guardar_expediente_documento(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)

    if request.method != "POST":
        return redirect("alumnos:index")

    documento_id = (request.POST.get("expediente_id") or "").strip()
    documento = None
    if documento_id:
        documento = get_object_or_404(ExpedienteDocumento, id=documento_id, alumno=alumno)

    nombre_documento = (request.POST.get("expediente_nombre_documento") or "").strip()
    tipo_documento = (request.POST.get("expediente_tipo_documento") or ExpedienteDocumento.TipoDocumento.OTRO).strip()
    fecha_emision_raw = (request.POST.get("expediente_fecha_emision") or "").strip()
    estado = (request.POST.get("expediente_estado") or ExpedienteDocumento.EstadoDocumento.VIGENTE).strip()
    observaciones = (request.POST.get("expediente_observaciones") or "").strip()
    archivo = request.FILES.get("expediente_archivo")

    if not nombre_documento:
        return redirect("alumnos:index")

    if documento is None:
        documento = ExpedienteDocumento(alumno=alumno)

    documento.nombre_documento = nombre_documento
    documento.tipo_documento = tipo_documento if tipo_documento in dict(ExpedienteDocumento.TipoDocumento.choices) else ExpedienteDocumento.TipoDocumento.OTRO
    try:
        documento.fecha_emision = date.fromisoformat(fecha_emision_raw) if fecha_emision_raw else None
    except ValueError:
        documento.fecha_emision = None
    documento.estado = estado if estado in dict(ExpedienteDocumento.EstadoDocumento.choices) else ExpedienteDocumento.EstadoDocumento.VIGENTE
    documento.observaciones = observaciones

    if archivo:
        if documento.archivo:
            documento.archivo.delete(save=False)
        documento.archivo = archivo

    documento.save()
    registrar_actividad(
        request,
        "ExpedienteDocumento",
        documento.id,
        "expediente_guardado",
        f"Documento de expediente: {documento.nombre_documento}",
        alumno=alumno,
    )
    return redirect("alumnos:index")


@never_cache
@admin_required
def eliminar_expediente_documento(request, alumno_id, documento_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    documento = get_object_or_404(ExpedienteDocumento, id=documento_id, alumno=alumno)

    if documento.archivo:
        documento.archivo.delete(save=False)

    registrar_actividad(
        request,
        "ExpedienteDocumento",
        documento.id,
        "expediente_eliminado",
        f"Documento eliminado: {documento.nombre_documento}",
        alumno=alumno,
    )
    documento.delete()
    return redirect("alumnos:index")


@never_cache
@admin_required
def ver_expediente_documento(request, alumno_id, documento_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    documento = get_object_or_404(ExpedienteDocumento, id=documento_id, alumno=alumno)

    if not documento.archivo:
        raise Http404("No se encontró el archivo solicitado.")

    archivo = default_storage.open(documento.archivo.name, "rb")
    response = FileResponse(archivo)
    nombre_archivo = os.path.basename(documento.archivo.name)
    response["Content-Disposition"] = f'inline; filename="{nombre_archivo}"'
    return response


@never_cache
@admin_required
def guardar_observacion_academica(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)

    if request.method != "POST":
        return redirect("alumnos:index")

    if not _is_directivo(request):
        return HttpResponseForbidden("Acceso denegado: solo Directivo puede editar historial académico.")

    observacion_id = (request.POST.get("observacion_id") or "").strip()
    observacion = None
    if observacion_id:
        observacion = get_object_or_404(ObservacionAcademica, id=observacion_id, alumno=alumno)

    periodo = (request.POST.get("observacion_periodo") or "").strip()
    conducta = (request.POST.get("observacion_conducta") or ObservacionAcademica.Conducta.BUENA).strip()
    texto = (request.POST.get("observacion_texto") or "").strip()

    if not texto:
        return redirect("alumnos:index")

    if observacion is None:
        observacion = ObservacionAcademica(alumno=alumno, creado_por=request.user)

    periodos_validos = {choice[0] for choice in PERIODO_CHOICES}
    observacion.periodo = periodo if periodo in periodos_validos else ""
    observacion.conducta = conducta if conducta in {choice[0] for choice in ObservacionAcademica.Conducta.choices} else ObservacionAcademica.Conducta.BUENA
    observacion.observacion = texto
    observacion.creado_por = request.user
    observacion.save()

    registrar_actividad(
        request,
        "ObservacionAcademica",
        observacion.id,
        "observacion_guardada",
        f"Observación académica: {alumno.apellido}, {alumno.nombre}",
        alumno=alumno,
    )
    return redirect("alumnos:index")


@never_cache
@admin_required
def eliminar_observacion_academica(request, alumno_id, observacion_id):
    if not _is_directivo(request):
        return HttpResponseForbidden("Acceso denegado: solo Directivo puede editar historial académico.")

    alumno = get_object_or_404(Alumno, id=alumno_id)
    observacion = get_object_or_404(ObservacionAcademica, id=observacion_id, alumno=alumno)

    registrar_actividad(
        request,
        "ObservacionAcademica",
        observacion.id,
        "observacion_eliminada",
        f"Observación académica eliminada: {alumno.apellido}, {alumno.nombre}",
        alumno=alumno,
    )
    observacion.delete()
    return redirect("alumnos:index")


@never_cache
def ficha_json(request, alumno_id):
    """Devuelve la información de la ficha del alumno y sus responsables en JSON."""

    if not request.user.is_authenticated:
        next_url = request.get_full_path()
        return redirect(f"{reverse('login')}?next={quote(next_url, safe='/')}")

    alumno = get_object_or_404(Alumno, id=alumno_id)

    responsables_data = []
    for r in alumno.responsables.all().order_by("n_orden", "apellido", "nombre"):
        responsables_data.append(
            {
                "id": r.id,
                "tipo_responsable": r.tipo_responsable,
                "nombre": r.nombre,
                "apellido": r.apellido,
                "dni": r.dni,
                "fecha_nacimiento": r.fecha_nacimiento.strftime("%Y-%m-%d"),
                "parentesco": r.parentesco,
                "telefono": r.telefono,
                "telefono_alternativo": r.telefono_alternativo,
                "correo_electronico": r.correo_electronico,
                "domicilio": r.domicilio,
                "localidad": r.localidad,
                "provincia": r.provincia,
                "codigo_postal": r.codigo_postal,
                "ocupacion": r.ocupacion,
                "lugar_trabajo": r.lugar_trabajo,
                "observaciones": r.observaciones,
                "n_orden": r.n_orden,
                "nacionalidad": r.nacionalidad,
                "profesion": r.profesion,
                "certificado_antivariolico": r.certificado_antivariolico,
                "certificado_antidifterico": r.certificado_antidifterico,
                "certificado_antipolio": r.certificado_antipolio,
                "certificado_buco_dental": r.certificado_buco_dental,
                "perimetral": r.perimetral,
                "perimetral_motivo": r.perimetral_motivo,
                "puede_retirar": r.puede_retirar,
                "anotaciones_particulares": r.anotaciones_particulares,
            }
        )

    expediente_data = []
    for doc in alumno.expediente_documentos.all().order_by("-fecha_carga", "-id"):
        expediente_data.append(
            {
                "id": doc.id,
                "nombre_documento": doc.nombre_documento,
                "tipo_documento": doc.tipo_documento,
                "tipo_documento_label": doc.get_tipo_documento_display(),
                "fecha_emision": _fecha_iso(doc.fecha_emision),
                "fecha_carga": doc.fecha_carga.strftime("%Y-%m-%d %H:%M") if doc.fecha_carga else "",
                "fecha_carga_label": doc.fecha_carga.strftime("%d/%m/%Y %H:%M") if doc.fecha_carga else "",
                "estado": doc.estado,
                "estado_label": _estado_documento_label(doc.estado),
                "archivo_nombre": os.path.basename(doc.archivo.name) if doc.archivo else "",
                "archivo_url": f"/alumnos/expediente/{alumno.id}/documento/{doc.id}/ver/" if doc.archivo else "",
                "observaciones": doc.observaciones,
            }
        )

    historial_academico = obtener_historial_academico(alumno)
    historial_anual = _serializar_historial_anual(alumno)

    historial_actividad = []
    for log in RegistroActividadAlumno.objects.filter(
        alumno=alumno,
        entidad__in=["Alumno", "ExpedienteDocumento", "ObservacionAcademica"],
    ).order_by("-fecha_hora", "-id")[:20]:
        historial_actividad.append(
            {
                "entidad": log.entidad,
                "objeto_id": log.objeto_id,
                "accion": log.accion,
                "descripcion": log.descripcion,
                "correo_electronico": log.correo_electronico,
                "fecha_hora": log.fecha_hora.strftime("%d/%m/%Y %H:%M"),
            }
        )

    data = {
        "alumno": {
            "id": alumno.id,
            "nombre": alumno.nombre,
            "apellido": alumno.apellido,
            "dni": alumno.dni,
                "tipo_identificacion": alumno.tipo_identificacion,
                "tipo_identificacion_label": alumno.get_tipo_identificacion_display(),
            "fecha_nacimiento": alumno.fecha_nacimiento.strftime("%Y-%m-%d"),
            "fecha_baja": alumno.fecha_baja.strftime("%Y-%m-%d") if alumno.fecha_baja else "",
            "motivo_baja": alumno.motivo_baja,
            "certificado_baja": alumno.certificado_baja,
            "certificado_baja_url": f"/alumnos/baja/certificado/{alumno.id}/" if alumno.certificado_baja else "",
            "domicilio": alumno.domicilio,
            "telefono": alumno.telefono_contacto,
            "curso": f"{alumno.anio}° {alumno.division}",
            "anio": alumno.anio,
            "division": alumno.division,
            "estado": "Activo" if alumno.activo else "Inactivo",
            "estado_promocion": alumno.estado_promocion,
            "estado_promocion_label": alumno.get_estado_promocion_display(),
            "motivo_no_promocion": alumno.motivo_no_promocion,
            "documentacion_completa": alumno.documentacion_completa,
            "documentacion_faltante": alumno.documentacion_faltante,
            "documentacion_total": len(alumno.documentacion_archivos),
            "expediente_total": len(expediente_data),
        },
        "responsables": responsables_data,
        "expediente_documentos": expediente_data,
        "historial_academico": historial_academico,
        "historial_academico_anual": historial_anual,
        "historial_actividad": historial_actividad,
        "permisos": {
            "puede_editar_historial": _is_directivo(request),
        },
    }

    return JsonResponse(data)



def quitar_documento(request, alumno_id, nombre):
    alumno = get_object_or_404(Alumno, id=alumno_id)

    nombre = str(nombre)
    ruta = os.path.join("alumnos", "documentacion", str(alumno.pk), nombre)

    if not default_storage.exists(ruta):
        raise Http404("No se encontró el archivo solicitado.")

    default_storage.delete(ruta)

    carpeta = os.path.join("alumnos", "documentacion", str(alumno.pk))
    if default_storage.exists(carpeta):
        _, archivos = default_storage.listdir(carpeta)
        if not archivos and alumno.documentacion:
            alumno.documentacion = None
            alumno.save(update_fields=["documentacion"])

    return redirect("alumnos:index")

