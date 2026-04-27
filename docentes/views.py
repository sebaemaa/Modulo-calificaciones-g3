from django.shortcuts import render
# from .models import Docente, Materia  # descomentar cuando empieces a usarlos

# ================================================================
# MÓDULO 4 — GESTIÓN DE DOCENTES Y MATERIAS
# Grupo responsable: [nombre del grupo]
# Editá solo este archivo. No toques views.py de otros módulos.
# URL base de este módulo: /docentes/
# ================================================================

def index(request):
    """Panel de docentes — punto de entrada del módulo."""
    return render(request, 'docentes/index.html')
