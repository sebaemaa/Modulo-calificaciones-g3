"""Rutas del Módulo 3 — Gestión de Calificaciones (se monta en /calificaciones/).

Las rutas del docente llevan el cuatrimestre (1 o 2) y el id de la materia,
por ejemplo: /calificaciones/profesor/1/7/planilla-calificaciones/
Se usa el id (y no el nombre) porque dos cursos pueden tener una materia con
el mismo nombre. Las rutas del alumno no llevan datos: el sistema usa la
ficha del usuario logueado.
"""
# path() sirve para unir una direccion (URL) con la funcion que la atiende.
from django.urls import path

# Importa views.py de esta misma carpeta (el punto significa "esta app").
from . import views

# Prefijo común de las pantallas del docente.
# <int:cuat> y <int:materia_id> son numeros que vienen en la URL y llegan a la vista como parametros.
DOCENTE = "profesor/<int:cuat>/<int:materia_id>/"

# Lista de rutas: Django la recorre de arriba a abajo hasta encontrar la que coincide.
urlpatterns = [
    # --- inicio del módulo (cambia según el rol) y publicación anual ---
    # /calificaciones/ -> menu del modulo. "name" es el apodo para usar en {% url %} y redirect().
    path("", views.menu, name="calificaciones_menu"),
    # Pantalla donde secretaria/directivo publica u oculta los boletines del año.
    path("publicar-boletines/", views.publicar_boletines, name="publicar_boletines"),

    # --- boletín (RITE) ---
    # Buscador de alumnos para elegir de quien ver el boletin (personal de la escuela).
    path("alumno/seleccionar/", views.alumno_seleccionar, name="alumno_seleccionar"),
    # Muestra el boletin (del alumno logueado o del elegido).
    path("boletin/", views.alumno_ver_boletin, name="alumno_ver_boletin"),
    # Recibe el clic de "firmar / tomar conocimiento" del boletin.
    path("boletin/confirmar/", views.confirmar_rite, name="confirmar_rite"),

    # --- docente: carga de notas (guardado automático) ---
    # Grilla donde el docente carga las notas.
    path(DOCENTE + "cargar-notas/", views.profesor_cargar_notas, name="profesor_cargar_notas"),
    # Guarda UNA nota (la llama el JavaScript cada vez que se cambia una celda).
    path(DOCENTE + "guardar-nota/", views.profesor_guardar_nota, name="profesor_guardar_nota"),
    # Guarda la valoracion TEA/TEP/TED de un alumno.
    path(DOCENTE + "guardar-valoracion/", views.profesor_guardar_valoracion, name="profesor_guardar_valoracion"),

    # --- docente: categorías de evaluación ---
    # Lista las categorias (columnas) de la materia.
    path(DOCENTE + "categorias/", views.profesor_categorias, name="profesor_categorias"),
    # Crea una categoria nueva.
    path(DOCENTE + "categorias/agregar/", views.profesor_agregar_categoria, name="profesor_agregar_categoria"),
    # Edita una categoria; <int:cat_id> es el id de la categoria.
    path(DOCENTE + "categorias/<int:cat_id>/editar/", views.profesor_editar_categoria, name="profesor_editar_categoria"),
    # Borra una categoria.
    path(DOCENTE + "categorias/<int:cat_id>/eliminar/", views.profesor_eliminar_categoria, name="profesor_eliminar_categoria"),

    # --- docente: importar notas desde Excel ---
    # Pantalla para subir el archivo Excel con notas.
    path(DOCENTE + "excel/", views.profesor_cargar_excel, name="profesor_cargar_excel"),
    # Confirma la importacion despues de ver la vista previa.
    path(DOCENTE + "excel/confirmar/", views.profesor_confirmar_excel, name="profesor_confirmar_excel"),
    # Descarga un Excel modelo ya armado con los alumnos y columnas.
    path(DOCENTE + "excel/plantilla/", views.profesor_descargar_plantilla, name="profesor_descargar_plantilla"),

    # --- planilla de calificaciones (docente; secretaría y directivo la ven) ---
    # Planilla de calificaciones: resumen del año, cierre y reapertura del cuatrimestre.
    path(DOCENTE + "planilla-calificaciones/", views.profesor_planilla, name="profesor_planilla"),
]
