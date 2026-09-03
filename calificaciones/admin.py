from django.contrib import admin
from .models import AlumnoCalificacion, CategoriaEvaluacion, NotaEvaluacion, BoletinConfig


@admin.register(AlumnoCalificacion)
class AlumnoCalificacionAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'dni', 'curso', 'division', 'materia')
    list_filter = ('materia', 'curso')
    search_fields = ('nombre', 'apellido', 'dni')


@admin.register(CategoriaEvaluacion)
class CategoriaEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'materia_nombre', 'orden')
    list_filter = ('materia_nombre',)
    ordering = ('materia_nombre', 'orden')


@admin.register(NotaEvaluacion)
class NotaEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('alumno_calificacion', 'categoria', 'cuatrimestre', 'valor', 'descripcion')
    list_filter = ('cuatrimestre', 'categoria__materia_nombre')
    search_fields = ('alumno_calificacion__nombre',)


@admin.register(BoletinConfig)
class BoletinConfigAdmin(admin.ModelAdmin):
    list_display = ('cuatrimestre', 'publicado', 'fecha_publicacion')
