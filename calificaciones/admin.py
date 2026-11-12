"""Registro en el admin de Django de los modelos del módulo.

Sirve para revisar y cargar datos rápido durante la exposición. Las pantallas
propias del módulo son las que usan docentes y alumnos; el admin es una ayuda
para el equipo.
"""
# Modulo del panel de administracion de Django (/admin/).
from django.contrib import admin

# Trae las tablas del modulo que se quieren ver en el admin.
from .models import (
    BoletinConfig,
    CategoriaEvaluacion,
    NotaEvaluacion,
    PublicacionBoletin,
)


# El decorador @admin.register conecta la tabla con esta configuracion del admin.
@admin.register(CategoriaEvaluacion)
# Configuracion de como se ve CategoriaEvaluacion en el admin.
class CategoriaEvaluacionAdmin(admin.ModelAdmin):
    # Columnas que se muestran en el listado.
    list_display = ('nombre', 'materia', 'orden')
    # Filtro lateral por materia.
    list_filter = ('materia',)
    # Orden del listado.
    ordering = ('materia', 'orden')


# Registra la tabla de notas en el admin.
@admin.register(NotaEvaluacion)
class NotaEvaluacionAdmin(admin.ModelAdmin):
    # Columnas del listado de notas.
    list_display = ('alumno', 'materia', 'categoria', 'cuatrimestre', 'valor', 'descripcion')
    # Filtros; categoria__nombre = "el nombre de la categoria" (el doble guion bajo cruza a otra tabla).
    list_filter = ('cuatrimestre', 'materia', 'categoria__nombre')
    # Buscador por nombre y apellido del alumno.
    search_fields = ('alumno__nombre', 'alumno__apellido')


# Registra la configuracion vieja del boletin.
@admin.register(BoletinConfig)
class BoletinConfigAdmin(admin.ModelAdmin):
    # Solo guarda la fecha de cierre de cada cuatrimestre.
    # Columnas del listado.
    list_display = ('cuatrimestre', 'publicado', 'fecha_publicacion')


# Registra la publicacion anual del boletin.
@admin.register(PublicacionBoletin)
class PublicacionBoletinAdmin(admin.ModelAdmin):
    # Interruptor anual del boletín: lo que se marque acá es lo que ven los alumnos.
    # Columnas del listado.
    list_display = ('anio', 'publicado', 'fecha_publicacion', 'usuario')
    # Filtro por publicado / no publicado.
    list_filter = ('publicado',)
    # El año mas nuevo primero.
    ordering = ('-anio',)
