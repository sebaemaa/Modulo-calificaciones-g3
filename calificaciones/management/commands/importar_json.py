import json
import os
from django.core.management.base import BaseCommand
from calificaciones.models import AlumnoCalificacion


class Command(BaseCommand):
    help = "Importa alumnos desde alumnos_data.json a la base de datos"

    def handle(self, *args, **options):
        ruta = os.path.join(os.path.dirname(__file__), '../../alumnos_data.json')
        ruta = os.path.normpath(ruta)

        if not os.path.exists(ruta):
            self.stderr.write(f"No se encontró {ruta}")
            return

        with open(ruta, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        AlumnoCalificacion.objects.all().delete()
        for item in datos:
            AlumnoCalificacion.objects.create(
                nombre=item['nombre'],
                curso=item['curso'],
                division=item['division'],
                materia=item['materia'],
                nota1=item['nota1'],
                nota2=item['nota2'],
            )

        self.stdout.write(self.style.SUCCESS(f"Importados {len(datos)} alumnos correctamente"))
