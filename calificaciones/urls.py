from django.urls import path
from . import views #lo que hace esta linea es decirle que desde la misma carpeta importe views.py

urlpatterns = [
    path("", views.inicio, name="inicio_calificaciones"),

    path("profesor/", views.profesor, name="profesor"),
    path("profesor/agregar/", views.agregar_alumno, name="agregar_alumno"),
    path("profesor/editar/<int:alumno_id>/", views.editar_alumno, name="editar_alumno"),

    path("alumno/", views.alumno, name="alumno"),
    path("alumno/mensajes/", views.mensajes, name="mensajes"),
    
]