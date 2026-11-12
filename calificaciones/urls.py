"""Rutas del Módulo 3 — Gestión de Calificaciones (se monta en /calificaciones/).

Las rutas del docente llevan el cuatrimestre (1 o 2) y el id de la materia,
por ejemplo: /calificaciones/profesor/1/7/planilla-calificaciones/
Se usa el id (y no el nombre) porque dos cursos pueden tener una materia con
el mismo nombre. Las rutas del alumno no llevan datos: el sistema usa la
ficha del usuario logueado.
"""
from django.urls import path

from . import views

# Prefijo común de las pantallas del docente.
DOCENTE = "profesor/<int:cuat>/<int:materia_id>/"

urlpatterns = [
    # --- inicio del módulo (cambia según el rol) y publicación anual ---
    path("", views.menu, name="calificaciones_menu"),
    path("publicar-boletines/", views.publicar_boletines, name="publicar_boletines"),

    # --- boletín (RITE) ---
    path("alumno/seleccionar/", views.alumno_seleccionar, name="alumno_seleccionar"),
    path("boletin/", views.alumno_ver_boletin, name="alumno_ver_boletin"),
    path("boletin/confirmar/", views.confirmar_rite, name="confirmar_rite"),

    # --- docente: carga de notas (guardado automático) ---
    path(DOCENTE + "cargar-notas/", views.profesor_cargar_notas, name="profesor_cargar_notas"),
    path(DOCENTE + "guardar-nota/", views.profesor_guardar_nota, name="profesor_guardar_nota"),
    path(DOCENTE + "guardar-valoracion/", views.profesor_guardar_valoracion, name="profesor_guardar_valoracion"),

    # --- docente: categorías de evaluación ---
    path(DOCENTE + "categorias/", views.profesor_categorias, name="profesor_categorias"),
    path(DOCENTE + "categorias/agregar/", views.profesor_agregar_categoria, name="profesor_agregar_categoria"),
    path(DOCENTE + "categorias/<int:cat_id>/editar/", views.profesor_editar_categoria, name="profesor_editar_categoria"),
    path(DOCENTE + "categorias/<int:cat_id>/eliminar/", views.profesor_eliminar_categoria, name="profesor_eliminar_categoria"),

    # --- docente: importar notas desde Excel ---
    path(DOCENTE + "excel/", views.profesor_cargar_excel, name="profesor_cargar_excel"),
    path(DOCENTE + "excel/confirmar/", views.profesor_confirmar_excel, name="profesor_confirmar_excel"),
    path(DOCENTE + "excel/plantilla/", views.profesor_descargar_plantilla, name="profesor_descargar_plantilla"),

    # --- planilla de calificaciones (docente; secretaría y directivo la ven) ---
    path(DOCENTE + "planilla-calificaciones/", views.profesor_planilla, name="profesor_planilla"),
]
