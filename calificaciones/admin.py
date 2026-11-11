"""Registro en el admin de Django de los modelos del módulo.

Sirve para revisar y cargar datos rápido durante la exposición. Las pantallas
propias del módulo son las que usan docentes y alumnos; el admin es una ayuda
para el equipo.
"""
from django.contrib import admin

from .models import (
    BoletinConfig,
    CategoriaEvaluacion,
    InasistenciaMateria,
    NotaEvaluacion,
    PublicacionBoletin,
)


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
    # Solo guarda la fecha de cierre de cada cuatrimestre.
    list_display = ('cuatrimestre', 'publicado', 'fecha_publicacion')


@admin.register(InasistenciaMateria)
class InasistenciaMateriaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'materia', 'cuatrimestre', 'cantidad')
    list_filter = ('cuatrimestre', 'materia')
    search_fields = ('alumno__nombre', 'alumno__apellido')


@admin.register(PublicacionBoletin)
class PublicacionBoletinAdmin(admin.ModelAdmin):
    # Interruptor anual del boletín: lo que se marque acá es lo que ven los alumnos.
    list_display = ('anio', 'publicado', 'fecha_publicacion', 'usuario')
    list_filter = ('publicado',)
    ordering = ('-anio',)
