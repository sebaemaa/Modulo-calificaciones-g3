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
]
