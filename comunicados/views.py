from django.shortcuts import render
# from .models import Comunicado  # descomentar cuando empieces a usarlo

# ================================================================
# MÓDULO 5 — COMUNICADOS Y NOTIFICACIONES
# Grupo responsable: [nombre del grupo]
# Editá solo este archivo. No toques views.py de otros módulos.
# URL base de este módulo: /comunicados/
# ================================================================

def index(request):
    """Panel de comunicados — punto de entrada del módulo."""
    return render(request, 'comunicados/index.html')
