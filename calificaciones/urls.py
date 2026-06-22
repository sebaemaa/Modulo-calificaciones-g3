from django.urls import path  # path(): función de Django que asocia una URL (string) con una función vista. Cada path() genera una entrada en la tabla de ruteo del proyecto
from . import views  # Importa el archivo views.py que está en la misma carpeta (calificaciones/). El punto (.) significa "mismo directorio"


urlpatterns = [  # urlpatterns es una lista de objetos path(). Django recorre esta lista de arriba a abajo hasta que encuentra el primer path() que coincide con la URL que pide el navegador
    path("", views.inicio, name="inicio_calificaciones"),  # Ruta vacía: /calificaciones/ → ejecuta la función views.inicio(). name es un identificador único para referenciar esta URL desde templates y vistas sin escribir la URL a mano
    path("profesor/", views.profesor, name="profesor"),  # /calificaciones/profesor/ → views.profesor(): muestra lista de cursos
    path("profesor/crear-curso/", views.crear_curso, name="crear_curso"),  # /calificaciones/profesor/crear-curso/ → formulario de creación de curso
    path("profesor/eliminar-curso/<int:curso_id>/", views.eliminar_curso, name="eliminar_curso"),  # <int:curso_id>: captura un número entero de la URL y lo pasa como parámetro curso_id a la función. Ej: /eliminar-curso/3/ → curso_id=3
    path("profesor/<int:curso_id>/", views.ver_curso, name="ver_curso"),  # /calificaciones/profesor/1/ → views.ver_curso(request, curso_id=1). Muestra la grilla de notas. IMPORTANTE: esta ruta debe ir DESPUÉS de rutas fijas como "profesor/crear-curso/" porque Django usa la primera coincidencia
    path("profesor/<int:curso_id>/agregar-evaluacion/", views.agregar_evaluacion, name="agregar_evaluacion"),  # /profesor/1/agregar-evaluacion/ → formulario para agregar columna de evaluación
    path("profesor/<int:curso_id>/eliminar-evaluacion/", views.eliminar_evaluacion, name="eliminar_evaluacion"),  # POST para eliminar una columna de evaluación (solo acepta POST por seguridad)
    path("profesor/<int:curso_id>/exportar/", views.exportar_csv, name="exportar_csv"),  # /profesor/1/exportar/ → descarga CSV con las notas del curso
    path("profesor/<int:curso_id>/importar/", views.importar_csv, name="importar_csv"),  # /profesor/1/importar/ → formulario para subir CSV
    path("profesor/<int:curso_id>/enviar-mensaje/", views.enviar_mensaje, name="enviar_mensaje"),  # /profesor/1/enviar-mensaje/ → página con formulario de mensaje + listado de enviados
    path("profesor/agregar/", views.agregar_alumno, name="agregar_alumno"),  # /calificaciones/profesor/agregar/ → formulario para agregar alumno a un curso
    path("profesor/editar/<int:alumno_id>/", views.editar_alumno, name="editar_alumno"),  # /profesor/editar/5/ → formulario para editar el alumno con ID=5
    path("profesor/eliminar/<int:alumno_id>/", views.eliminar_alumno, name="eliminar_alumno"),  # GET: elimina al alumno con ese ID y redirige al curso
    path("consultar/", views.consultar, name="consultar"),  # /calificaciones/consultar/ → página para que el alumno ingrese su DNI
    path("mis-notas/", views.mis_notas, name="mis_notas"),  # /calificaciones/mis-notas/?dni=12345678 → muestra las notas del alumno con ese DNI
    path("mis-notas/mensajes/", views.mensajes, name="mensajes"),  # /calificaciones/mis-notas/mensajes/?dni=12345678 → mensajes del profesor para ese alumno
    path("profesor/reportar/<int:alumno_id>/", views.reportar_alumno, name="reportar_alumno"),  # /profesor/reportar/5/ → formulario para reportar alumno ID=5 a dirección
    path("profesor/reportes/eliminar/<int:reporte_id>/", views.eliminar_reporte, name="eliminar_reporte"),  # GET: elimina el reporte con ese ID
    path("profesor/reportes/curso/<int:curso_id>/", views.reportes_curso, name="reportes_curso"),  # /profesor/reportes/curso/1/ → lista todos los reportes del curso ID=1
    path("profesor/mensajes/eliminar/<int:mensaje_id>/", views.eliminar_mensaje, name="eliminar_mensaje"),  # GET: elimina el mensaje con ese ID y redirige a la página de mensajes del curso
]
