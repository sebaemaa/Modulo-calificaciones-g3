from django.urls import path
from . import views

urlpatterns = [
    path("", views.menu, name="calificaciones_menu"),

    path("profesor/seleccionar/", views.profesor_seleccionar_materia, name="profesor_seleccionar"),
    path("profesor/<int:cuat>/<str:materia>/", views.profesor_ver_alumnos, name="profesor_ver_alumnos"),
    path("profesor/<int:cuat>/<str:materia>/guardar/", views.profesor_guardar_nota, name="profesor_guardar_nota"),
    path("profesor/<int:cuat>/<str:materia>/categorias/", views.profesor_categorias, name="profesor_categorias"),
    path("profesor/<str:materia>/alumnos/", views.profesor_listar_alumnos, name="profesor_listar_alumnos"),
    path("profesor/<str:materia>/alumnos/agregar/", views.profesor_agregar_alumno, name="profesor_agregar_alumno"),
    path("profesor/<str:materia>/alumnos/editar/<int:alumno_id>/", views.profesor_editar_alumno, name="profesor_editar_alumno"),
    path("profesor/<str:materia>/alumnos/eliminar/<int:alumno_id>/", views.profesor_eliminar_alumno, name="profesor_eliminar_alumno"),
    path("profesor/<int:cuat>/<str:materia>/categorias/agregar/", views.profesor_agregar_categoria, name="profesor_agregar_categoria"),
    path("profesor/<int:cuat>/<str:materia>/categorias/editar/<int:cat_id>/", views.profesor_editar_categoria, name="profesor_editar_categoria"),
    path("profesor/<int:cuat>/<str:materia>/categorias/eliminar/<int:cat_id>/", views.profesor_eliminar_categoria, name="profesor_eliminar_categoria"),
    path("profesor/<int:cuat>/<str:materia>/cargar/", views.profesor_cargar_notas, name="profesor_cargar_notas"),
    path("profesor/<int:cuat>/<str:materia>/excel/", views.profesor_cargar_excel, name="profesor_cargar_excel"),
    path("profesor/<int:cuat>/<str:materia>/excel/confirmar/", views.profesor_confirmar_excel, name="profesor_confirmar_excel"),
    path("profesor/<int:cuat>/<str:materia>/excel/descargar/", views.profesor_descargar_plantilla, name="profesor_descargar_plantilla"),
    path("profesor/boletin/<int:cuat>/", views.profesor_toggle_boletin, name="profesor_toggle_boletin"),

    path("alumno/seleccionar/", views.alumno_seleccionar, name="alumno_seleccionar"),
    path("alumno/", views.alumno_ver_calificaciones, name="alumno_ver_calificaciones"),
    path("boletin/", views.alumno_ver_boletin, name="alumno_ver_boletin"),
    path("boletin/<int:cuat>/", views.alumno_ver_boletin, name="alumno_ver_boletin_cuat"),
]
