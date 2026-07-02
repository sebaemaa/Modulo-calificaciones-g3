from django.urls import path #importa la funcionalidad path de django es la herramienta que usa Django para definir "esta URL ejecuta esta vista
from . import views #lo que hace esta linea es decirle que desde la misma carpeta importe views.py

urlpatterns = [
    path("", views.inicio, name="inicio_calificaciones"), #esto quiere decir que cuando se visite la url principal del mudulo de calificaciones nos lleve al inicio
    path("profesor/", views.profesor, name="profesor"),#aca lo mismo pero cuando visitemos la url calificaciones/profesor/ nos lleva a la vista del profesor
    path("profesor/agregar/", views.agregar_alumno, name="agregar_alumno"),#aca tambien """"/Agregar/ nos lleve a la seccion agregar alumno 
    path("profesor/editar/<int:alumno_id>/", views.editar_alumno, name="editar_alumno"),#aca creamos una url dinamica 
    path("profesor/editar/<int:alumno_id>/", views.editar_alumno, name="editar_alumno"),
    
    path("alumno/", views.alumno, name="alumno"),#basicamente lo mismo cuando el usuario solicite ir a vista alumnos llama a la funcion views del mismo 
    #directorio y ejecuta el html 
    path("alumno/mensajes/", views.mensajes, name="mensajes"),
    
    #"" es la url inicial  
    # cuando se usa views."" quiere decir que es lo que se va ejecutar cuando llegue la solicitud 
    # el name es basicamente eso darle un apodo a la url para que django la encuentre cuando se pide 
    
    
    
]