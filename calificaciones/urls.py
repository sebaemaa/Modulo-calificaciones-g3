from django.urls import path  # Importa la función 'path' necesaria para definir rutas de URL
from . import views  # Importa el archivo views.py de tu carpeta actual para poder llamar a las funciones ahí definidas

urlpatterns = [  # Lista que contiene todas las rutas (URLs) configuradas para esta aplicación
    path("", views.inicio, name="inicio_calificaciones"),  # La URL raíz de la app (ej: /calificaciones/), llama a la función 'inicio'

    path("profesor/", views.profesor, name="profesor"),  # URL para la vista general del profesor
    path("profesor/agregar/", views.agregar_alumno, name="agregar_alumno"),  # URL para el formulario de crear un nuevo alumno
    path("profesor/editar/<int:alumno_id>/", views.editar_alumno, name="editar_alumno"),  # URL dinámica: espera un ID de alumno (entero) para editar un registro específico

    path("alumno/", views.alumno, name="alumno"),  # URL para la vista principal del alumno
    path("alumno/mensajes/", views.mensajes, name="mensajes"),  # URL para ver los mensajes del alumno
]