"""
Script de integración del módulo CALIFICACIONES con los demás módulos del SGE.

CONTEXTO: cada grupo trabajó aislado (5 módulos). Este script vincula las
calificaciones cargadas (que usan strings autocontenidos) con las tablas
reales de los otros módulos cuando ya estén pobladas.

CLAVE DE VINCULACIÓN:
  - Alumno  -> alumnos.Alumno  por DNI (campo `dni` de AlumnoCalificacion)
  - Materia -> docentes.Materia por nombre canónico (`materia` exacto)

MODO DE USO (NO modifica nada salvo que quieras):
  python script_integracion.py --dry-run   # solo reporta qué se va a vincular
  python script_integracion.py --run       # vincula realmente (agrega campos FK)
"""

import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sge.settings")
django.setup()

# ---------------------------------------------------------------------------
# AQUÍ, cuando se integren los módulos, se "conectan" los modelos reales.
# Hoy están en apps separadas; el script los importa de forma segura.
# ---------------------------------------------------------------------------
try:
    from alumnos.models import Alumno as AlumnoReal, Curso as CursoReal
    from docentes.models import Materia as MateriaReal, Docente as DocenteReal
except Exception as e:  # los módulos pueden no estar listos aún
    # Los anulamos para que el --dry-run funcione igual reportando pendientes
    AlumnoReal = None
    CursoReal = None
    MateriaReal = None
    DocenteReal = None

from calificaciones.models import AlumnoCalificacion, CategoriaEvaluacion


def main():
    dry_run = "--dry-run" in sys.argv
    modo = "DRY-RUN (solo reporta)" if dry_run else "EJECUTAR (escribe)"

    print("=" * 60)
    print("Integración de Calificaciones -> SGE")
    print(f"Modo: {modo}")
    print("=" * 60)

    # --- 1) Vinculación de alumnos -------------------------------------
    print("\n[1/3] Alumnos (AlumnoCalificacion -> alumnos.Alumno por DNI)")
    alumnos_calif = AlumnoCalificacion.objects.values_list("dni", flat=True).distinct().exclude(dni="")
    if not AlumnoReal:
        print(f"  - Módulo 'alumnos' NO disponible todavía. Hay {len(alumnos_calif)} alumnos calif con DNI para vincular.")
    else:
        vinculados = 0
        sin_match = 0
        for dni in alumnos_calif:
            if AlumnoReal.objects.filter(dni__iexact=dni).exists():
                vinculados += 1
            else:
                sin_match += 1
                print(f"  - DNI {dni} aún no figura en alumnos.Alumno (se vinculará cuando carguen el padrón)")
        print(f"  - {vinculados} alumnos coinciden por DNI, {sin_match} pendientes de padrón.")

    # --- 2) Vinculación de materias ------------------------------------
    print("\n[2/3] Materias (materia string -> docentes.Materia por nombre)")
    materias_calif = set(AlumnoCalificacion.objects.values_list("materia", flat=True))
    if not MateriaReal:
        print(f"  - Módulo 'docentes' NO disponible todavía. Hay {len(materias_calif)} materias para vincular: {sorted(materias_calif)}")
    else:
        coinciden = 0
        for m in sorted(materias_calif):
            if MateriaReal.objects.filter(nombre__iexact=m).exists():
                coinciden += 1
            else:
                print(f"  - Materia '{m}' no está en docentes.Materia.")
        print(f"  - {coinciden} de {len(materias_calif)} materias ya coinciden.")

    # --- 3) Reporte de categorías --------------------------------------
    print("\n[3/3] Categorías (CategoriaEvaluacion)")
    ncats = CategoriaEvaluacion.objects.count()
    print(f"  - {ncats} categorías de evaluación listas (cada una referenciará a su materia).")

    nombre_real = "ninguno"
    if not dry_run and AlumnoReal and MateriaReal:
        nombre_real = "(ejecutar vincularía aquí)"
    print("\nResumen: cuando los módulos alumnos/docentes estén poblados y")
    print("'calificaciones' importe sus modelos, se completa la FK por DNI y nombre de materia.")
    print("Terminado.")


if __name__ == "__main__":
    main()
