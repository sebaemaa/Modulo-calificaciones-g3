"""
Comando para cargar cursos de ejemplo en el módulo de calificaciones.
El profesor agrega los alumnos manualmente desde la interfaz.

Uso: python manage.py cargar_datos_ejemplo
"""
from django.core.management.base import BaseCommand
from calificaciones.models import Curso


CURSOS = [
    {"año": 2026, "curso": "1°", "division": "A", "materia": "Matemática"},
    {"año": 2026, "curso": "1°", "division": "A", "materia": "Lengua"},
    {"año": 2026, "curso": "2°", "division": "B", "materia": "Matemática"},
    {"año": 2026, "curso": "3°", "division": "A", "materia": "Historia"},
]


class Command(BaseCommand):
    help = "Carga cursos de ejemplo en el módulo de calificaciones"

    def handle(self, *args, **options):
        for c in CURSOS:
            curso, creado = Curso.objects.get_or_create(**c)
            status = "+" if creado else "~"
            self.stdout.write(f"  {status} Curso: {curso}")
        self.stdout.write(self.style.SUCCESS("Cursos de ejemplo cargados correctamente."))
