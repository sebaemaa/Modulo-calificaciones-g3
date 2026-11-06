from django.contrib import admin
from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'docente', 'alumno')
    list_filter = ('rol',)
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    raw_id_fields = ('docente', 'alumno')
