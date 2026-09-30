from django.contrib import admin
from .models import CategoriaEvaluacion, NotaEvaluacion, BoletinConfig


@admin.register(CategoriaEvaluacion)
class CategoriaEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'materia', 'orden')
    list_filter = ('materia',)
    ordering = ('materia', 'orden')


@admin.register(NotaEvaluacion)
class NotaEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'materia', 'categoria', 'cuatrimestre', 'valor', 'descripcion')
    list_filter = ('cuatrimestre', 'materia', 'categoria__nombre')
    search_fields = ('alumno__nombre', 'alumno__apellido')


@admin.register(BoletinConfig)
class BoletinConfigAdmin(admin.ModelAdmin):
    list_display = ('cuatrimestre', 'publicado', 'fecha_publicacion')