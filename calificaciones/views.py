from django.shortcuts import render
# from .models import Calificacion  # descomentar cuando empieces a usarlo

# ================================================================
# MÓDULO 3 — GESTIÓN DE CALIFICACIONES
# Grupo responsable: [nombre del grupo]
# Editá solo este archivo. No toques views.py de otros módulos.
# URL base de este módulo: /calificaciones/
# ================================================================

def index(request):
    """Panel de calificaciones — punto de entrada del módulo."""
    return render(request, 'calificaciones/index.html')
