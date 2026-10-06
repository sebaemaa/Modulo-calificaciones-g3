# Importa las herramientas del panel de administración de django
from django.contrib import admin

# Importa los modelos desde models.py
from .models import (
    Comunicado,
    LecturaComunicado
)

# Registra los modelos en el panel de administración.
admin.site.register(Comunicado)

admin.site.register(LecturaComunicado)