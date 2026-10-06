from django.urls import path
from . import views

app_name = "comunicados"

urlpatterns = [

    # Pantalla principal
    path(
        "",
        views.index,
        name="index"
    ),
    
    #Directivo
    path(
        "directivo/",
        views.directivo,
        name="directivo"
    ),

    path(
        "eliminar/<int:id>/",
        views.eliminar,
        name="eliminar"
    ),

    #Alumno
    path(
        "alumno/",
        views.alumno,
        name="alumno"
    ),

    path(
        "leer/<int:id>/",
        views.marcar_leido,
        name="leer"
    ),

    path(
        "archivar/<int:id>/",
        views.archivar,
        name="archivar"
    ),

    path(
        "ocultar/<int:id>/",
        views.ocultar,
        name="ocultar"
    ),

    # PDF
    path(
        "pdf/<int:id>/",
        views.ver_pdf,
        name="ver_pdf"
    ),
]