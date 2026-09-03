import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sge.settings")
django.setup()

from calificaciones.models import AlumnoCalificacion, CategoriaEvaluacion, NotaEvaluacion, BoletinConfig

MATERIAS = ["Matemática", "Lengua", "Historia"]
ALUMNOS = ["García, Lucía", "López, Martín", "Pérez, Sofía", "Rodríguez, Joaquín"]
CURSOS = [(7, "A"), (7, "A"), (7, "A"), (7, "A")]

CATS = ["Trabajo Práctico", "Examen", "Participación en clase"]

print("Borrando datos existentes...")
NotaEvaluacion.objects.all().delete()
CategoriaEvaluacion.objects.all().delete()
AlumnoCalificacion.objects.all().delete()
BoletinConfig.objects.all().delete()

print("Creando alumnos...")
for materia in MATERIAS:
    for i, nombre in enumerate(ALUMNOS):
        AlumnoCalificacion.objects.create(
            nombre=nombre,
            curso=str(CURSOS[i][0]),
            division=CURSOS[i][1],
            materia=materia,
        )

print("Creando categorías...")
for materia in MATERIAS:
    for orden, cat in enumerate(CATS, start=1):
        CategoriaEvaluacion.objects.create(
            nombre=cat,
            materia_nombre=materia,
            orden=orden,
        )

print("Creando notas de ejemplo...")
# Notas de ejemplo (nota promedio ~8 para García y Pérez, ~5 para López y Rodríguez)
import random
random.seed(42)
for alc in AlumnoCalificacion.objects.all():
    cats = CategoriaEvaluacion.objects.filter(materia_nombre=alc.materia)
    base = 8 if alc.nombre in ("García, Lucía", "Pérez, Sofía") else 5
    for cat in cats:
        for cuat in (1, 2):
            valor = base + random.choice([-1, 0, 0, 1, 2])
            valor = max(1, min(10, valor))
            NotaEvaluacion.objects.create(
                alumno_calificacion=alc,
                categoria=cat,
                cuatrimestre=cuat,
                valor=valor,
                descripcion="",
            )

BoletinConfig.objects.create(cuatrimestre=1, publicado=False)
BoletinConfig.objects.create(cuatrimestre=2, publicado=False)

print("¡Datos de ejemplo creados!")
print(f"  Alumnos: {AlumnoCalificacion.objects.count()}")
print(f"  Categorías: {CategoriaEvaluacion.objects.count()}")
print(f"  Notas: {NotaEvaluacion.objects.count()}")
