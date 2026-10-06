from django.urls import path
from . import views

app_name = "alumnos"
urlpatterns = [
    path("", views.index, name="index"),
    path("inactivos/", views.inactivos, name="inactivos"),
    path("baja/<int:id>/", views.dar_baja, name="dar_baja"),
    path("baja/certificado/<int:alumno_id>/", views.ver_certificado_baja, name="ver_certificado_baja"),
    path("promocion-curso/resumen/", views.promocion_curso_resumen, name="promocion_curso_resumen"),
    path("promocion-curso/confirmar/", views.confirmar_promocion_curso, name="confirmar_promocion_curso"),
    path("editar/<int:id>/", views.editar, name="editar"),
    path("reporte/", views.reporte, name="reporte"),
    path("<int:alumno_id>/ficha/", views.ficha_json, name="ficha_json"),
    path("expediente/<int:alumno_id>/documento/guardar/", views.guardar_expediente_documento, name="guardar_expediente_documento"),
    path("expediente/<int:alumno_id>/documento/<int:documento_id>/eliminar/", views.eliminar_expediente_documento, name="eliminar_expediente_documento"),
    path("expediente/<int:alumno_id>/documento/<int:documento_id>/ver/", views.ver_expediente_documento, name="ver_expediente_documento"),
    path("academico/<int:alumno_id>/observacion/guardar/", views.guardar_observacion_academica, name="guardar_observacion_academica"),
    path("academico/<int:alumno_id>/observacion/<int:observacion_id>/eliminar/", views.eliminar_observacion_academica, name="eliminar_observacion_academica"),
    path("documentacion/<int:alumno_id>/<path:nombre>/", views.ver_documento, name="ver_documento"),
    path("documentacion/quitar/<int:alumno_id>/<path:nombre>/", views.quitar_documento, name="quitar_documento"),
]

 