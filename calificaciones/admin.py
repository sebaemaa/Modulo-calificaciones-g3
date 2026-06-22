from django.contrib import admin
from .models import Curso, Alumno, Evaluacion


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    """Administración de cursos."""
    list_display = ("año", "curso", "division", "materia")
    list_filter = ("año", "materia")
    search_fields = ("materia", "curso")


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    """Administración de alumnos."""
    list_display = ("nombre", "dni", "curso")
    list_filter = ("curso__materia", "curso__curso", "curso__año")
    search_fields = ("nombre", "dni")


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    """Administración de evaluaciones."""
    list_display = ("alumno", "tipo", "valor")
    list_filter = ("tipo", "alumno__curso__materia")
    search_fields = ("alumno__nombre", "tipo")
