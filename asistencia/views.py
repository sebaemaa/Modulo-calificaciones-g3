from django.shortcuts import render
# from .models import RegistroAsistencia  # descomentar cuando empieces a usarlo

# ================================================================
# MÓDULO 2 — GESTIÓN DE ASISTENCIA
# Grupo responsable: [nombre del grupo]
# Editá solo este archivo. No toques views.py de otros módulos.
# URL base de este módulo: /asistencia/
# ================================================================

def index(request):
    """Panel de asistencia — punto de entrada del módulo."""
    return render(request, 'asistencia/index.html')
