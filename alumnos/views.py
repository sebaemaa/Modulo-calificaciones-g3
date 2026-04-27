from django.shortcuts import render
# from .models import Alumno, Curso  # descomentar cuando empieces a usarlos

# ================================================================
# MÓDULO 1 — GESTIÓN DE ALUMNOS
# Grupo responsable: [nombre del grupo]
# Editá solo este archivo. No toques views.py de otros módulos.
# URL base de este módulo: /alumnos/
# ================================================================

def index(request):
    """Lista de alumnos — punto de entrada del módulo."""
    return render(request, 'alumnos/index.html')
