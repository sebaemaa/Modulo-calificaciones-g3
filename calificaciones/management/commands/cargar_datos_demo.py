"""Carga los datos de demostración del módulo de calificaciones.

Uso:
    python manage.py cargar_datos_demo

Reproduce los datos de ejemplo de las maquetas de diseño:
- Docentes: Ana Martínez con Laboratorio de Programación (5° B),
  Sistemas digitales (5° B) y Laboratorio de Aplicaciones (5° A); Carlos Russo
  con Historia, Inglés, Análisis Matemático y Teleinformática (5° B).
- Alumno: Acosta, Lucía (5° B) con notas en las 6 materias del curso.
- Categorías con grupo y peso: TP 1 y TP 2 (Trabajos prácticos, 30 c/u)
  y Eval. 1 (Evaluación, 40) => la calificación se calcula ponderada.
- Asistencias del ciclo: Lucía tiene 4 faltas en LabProg (84 %, aprueba) y
  3 en Inglés (70 %, no acredita por la regla del 80 %).
- Usuarios: profesor1 y profesor2 (docentes), preceptora (secretaría) y
  sebaema (alumna Acosta, Lucía), clave prueba1234.
- Boletín anual oculto por defecto: la preceptora lo publica desde el menú
  con el botón "Publicar boletines del año".

El comando es idempotente: primero borra lo que haya creado en una corrida
anterior, así que se puede ejecutar todas las veces que haga falta.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from alumnos.models import Alumno, Curso
from asistencia.models import RegistroAsistencia
from cuentas.models import Perfil
from docentes.models import Docente, Materia

from calificaciones.models import (
    BoletinConfig,
    CategoriaEvaluacion,
    CierreCuatrimestre,
    ConfirmacionRite,
    NotaEvaluacion,
    PublicacionBoletin,
)

CUAT = 1
CLAVE = "prueba1234"

DNI_DOCENTES_DEMO = ["91000001", "91000009"]
DNI_ALUMNOS_DEMO = [f"910000{n:02d}" for n in range(1, 11)]
USUARIOS_DEMO = ["profesor1", "profesor2", "preceptora", "sebaema", "acosta.lucia"]


class Command(BaseCommand):
    help = "Carga los datos de demostración del módulo de calificaciones."

    def handle(self, *args, **options):
        self._limpiar()

        cu5a, _ = Curso.objects.get_or_create(anio=5, division="A")
        cu5b, _ = Curso.objects.get_or_create(anio=5, division="B")

        ana, _ = Docente.objects.update_or_create(
            dni="91000001",
            defaults={"nombre": "Ana", "apellido": "Martínez"},
        )
        carlos, _ = Docente.objects.update_or_create(
            dni="91000009",
            defaults={"nombre": "Carlos", "apellido": "Russo"},
        )

        labprog = Materia.objects.create(nombre="Laboratorio de Programación", curso=cu5b, docente=ana)
        sistdig = Materia.objects.create(nombre="Sistemas digitales", curso=cu5b, docente=ana)
        labaplic = Materia.objects.create(nombre="Laboratorio de Aplicaciones", curso=cu5a, docente=ana)
        historia = Materia.objects.create(nombre="Historia", curso=cu5b, docente=carlos)
        ingles = Materia.objects.create(nombre="Inglés", curso=cu5b, docente=carlos)
        analisis = Materia.objects.create(nombre="Análisis Matemático", curso=cu5b, docente=carlos)
        teleinfo = Materia.objects.create(nombre="Teleinformática", curso=cu5b, docente=carlos)

        lucia = self._alumno(cu5b, "Lucía", "Acosta", "91000001")
        tomas = self._alumno(cu5b, "Tomás", "Bravo", "91000002")
        nahuel = self._alumno(cu5b, "Nahuel", "Cáceres", "91000003")
        julieta = self._alumno(cu5b, "Julieta", "Domínguez", "91000004")
        mateo = self._alumno(cu5b, "Mateo", "Escobar", "91000005")
        camila = self._alumno(cu5b, "Camila", "Fernández", "91000006")
        pedro = self._alumno(cu5a, "Pedro", "Gómez", "91000007")
        sofia = self._alumno(cu5a, "Sofía", "Herrera", "91000008")
        ramiro = self._alumno(cu5a, "Ramiro", "Ibáñez", "91000009")
        ana_j = self._alumno(cu5a, "Ana", "Juárez", "91000010")

        tp1, tp2, ev1 = self._cats_tp_eval(labprog)
        sd_tp1, sd_tp2, sd_ev1 = self._cats_tp_eval(sistdig)
        la_tp1, la_tp2, la_ev1 = self._cats_tp_eval(labaplic)

        cat_historia = self._cat(historia, "Calificación", 1)
        cat_ingles = self._cat(ingles, "Calificación", 1)
        cat_analisis = self._cat(analisis, "Calificación", 1)
        cat_teleinfo = self._cat(teleinfo, "Calificación", 1)

        notas_labprog = {
            lucia: (8, 9, 8),
            tomas: (5, 6, 4),
            nahuel: (7, 7, 8),
            julieta: (9, 10, 9),
            mateo: (6, 5, 6),
            camila: (10, 9, 10),
        }
        for alumno, (n1, n2, n3) in notas_labprog.items():
            self._nota(alumno, labprog, tp1, n1)
            self._nota(alumno, labprog, tp2, n2)
            self._nota(alumno, labprog, ev1, n3)

        valoraciones = {
            lucia: "TEA", tomas: "TEP", nahuel: "TEA",
            julieta: "TEA", mateo: "TEP", camila: "TEA",
        }
        for alumno, valoracion in valoraciones.items():
            CierreCuatrimestre.objects.create(
                alumno=alumno, materia=labprog, cuatrimestre=CUAT,
                valoracion_preliminar=valoracion,
                cursada="R" if alumno is nahuel else "C",
            )

        CierreCuatrimestre.objects.filter(
            alumno=tomas, materia=labprog, cuatrimestre=CUAT,
        ).update(
            intensificacion=True, calificacion=Decimal("5"), calificacion_final=Decimal("7"),
        )

        notas_labprog_2c = {
            lucia: (9, 8),
            tomas: (7, 7),
            nahuel: (8, 7),
            julieta: (10, 9),
            mateo: (4, 5),
        }
        for alumno, (n1, n2) in notas_labprog_2c.items():
            self._nota(alumno, labprog, tp1, n1, cuat=2)
            self._nota(alumno, labprog, tp2, n2, cuat=2)

        cierres_2c = {
            lucia: ("TEA", "8", "8"),
            tomas: ("TEP", "7", "7"),
            nahuel: ("TEA", "7", "7"),
            julieta: ("TEA", "9", "9"),
            mateo: ("TED", "4", None),
        }
        for alumno, (valoracion, calif, final) in cierres_2c.items():
            CierreCuatrimestre.objects.create(
                alumno=alumno, materia=labprog, cuatrimestre=2,
                valoracion_preliminar=valoracion,
                calificacion=Decimal(calif),
                calificacion_final=Decimal(final) if final else None,
            )

        self._nota(lucia, sistdig, sd_tp1, 9)
        self._nota(lucia, sistdig, sd_tp2, 9)
        self._nota(lucia, sistdig, sd_ev1, 9)
        self._nota(mateo, sistdig, sd_tp1, 6)
        self._nota(mateo, sistdig, sd_tp2, 7)
        self._nota(mateo, sistdig, sd_ev1, 6)

        self._nota(pedro, labaplic, la_tp1, 8)
        self._nota(pedro, labaplic, la_tp2, 7)
        self._nota(pedro, labaplic, la_ev1, 9)
        self._nota(sofia, labaplic, la_tp1, 9)
        self._nota(sofia, labaplic, la_tp2, 9)
        self._nota(sofia, labaplic, la_ev1, 8)
        self._nota(ramiro, labaplic, la_tp1, 7)
        self._nota(ramiro, labaplic, la_ev1, 8)
        self._nota(ana_j, labaplic, la_ev1, 6)

        self._nota(lucia, historia, cat_historia, 7)
        self._nota(lucia, ingles, cat_ingles, 8)
        self._nota(lucia, analisis, cat_analisis, 6)
        self._nota(lucia, teleinfo, cat_teleinfo, 5)

        CierreCuatrimestre.objects.create(
            alumno=lucia, materia=teleinfo, cuatrimestre=CUAT,
            valoracion_preliminar="TEP", calificacion=Decimal("5"),
            intensificacion=True, calificacion_final=Decimal("7"),
        )
        self._nota(lucia, teleinfo, cat_teleinfo, 7, cuat=2)
        CierreCuatrimestre.objects.create(
            alumno=lucia, materia=teleinfo, cuatrimestre=2,
            valoracion_preliminar="TEP", calificacion=Decimal("7"),
        )

        ConfirmacionRite.objects.create(
            alumno=lucia, cuatrimestre=CUAT, tipo="adulto", usuario="seed",
        )
        ConfirmacionRite.objects.create(
            alumno=lucia, cuatrimestre=CUAT, tipo="estudiante", usuario="sebaema",
        )

        alumnos_5b = [lucia, tomas, nahuel, julieta, mateo, camila]
        faltas_lucia_labprog = {
            date(2026, 4, 14), date(2026, 5, 5),
            date(2026, 5, 26), date(2026, 6, 16),
        }
        faltas_lucia_ingles = {
            date(2026, 3, 11), date(2026, 4, 8), date(2026, 4, 29),
        }

        fechas_labprog = (
            self._fechas_semanales(date(2026, 3, 3), 16)
            + self._fechas_semanales(date(2026, 8, 4), 10)
        )
        fechas_ingles = self._fechas_semanales(date(2026, 3, 4), 10)

        registros = []
        for fecha in fechas_labprog:
            for alumno in alumnos_5b:
                estado = "A" if alumno is lucia and fecha in faltas_lucia_labprog else "P"
                registros.append(RegistroAsistencia(
                    alumno=alumno, materia=labprog, fecha=fecha, estado=estado,
                ))
        for fecha in fechas_ingles:
            for alumno in alumnos_5b:
                estado = "A" if alumno is lucia and fecha in faltas_lucia_ingles else "P"
                registros.append(RegistroAsistencia(
                    alumno=alumno, materia=ingles, fecha=fecha, estado=estado,
                ))
        RegistroAsistencia.objects.bulk_create(registros)

        PublicacionBoletin.objects.update_or_create(
            anio=timezone.now().year,
            defaults={"publicado": False, "fecha_publicacion": None, "usuario": ""},
        )

        u_prof = User.objects.create_user("profesor1", password=CLAVE)
        u_prof.first_name = "Ana"
        u_prof.last_name = "Martínez"
        u_prof.save()
        Perfil.objects.create(usuario=u_prof, rol=Perfil.DOCENTE, docente=ana)

        u_prof2 = User.objects.create_user("profesor2", password=CLAVE)
        u_prof2.first_name = "Carlos"
        u_prof2.last_name = "Russo"
        u_prof2.save()
        Perfil.objects.create(usuario=u_prof2, rol=Perfil.DOCENTE, docente=carlos)

        u_preceptora = User.objects.create_user("preceptora", password=CLAVE)
        u_preceptora.first_name = "Paula"
        u_preceptora.last_name = "Sosa"
        u_preceptora.save()
        Perfil.objects.create(usuario=u_preceptora, rol=Perfil.ADMINISTRATIVO)

        u_alum = User.objects.create_user("sebaema", password=CLAVE)
        u_alum.first_name = "Lucía"
        u_alum.save()
        Perfil.objects.create(usuario=u_alum, rol=Perfil.ALUMNO, alumno=lucia)

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados:"))
        self.stdout.write(f"  profesor1 / {CLAVE} -> Ana Martínez (3 materias)")
        self.stdout.write(f"  profesor2 / {CLAVE} -> Carlos Russo (4 materias)")
        self.stdout.write(f"  preceptora / {CLAVE} -> Paula Sosa (secretaría: ve todas las planillas)")
        self.stdout.write(f"  sebaema / {CLAVE} -> Acosta, Lucía (5° B)")
        self.stdout.write("  Materias Ana: LabProg 5B (100%), SistDig 5B (33%), LabAplic 5A (75%)")
        self.stdout.write("  Materias Carlos: Historia, Inglés, Análisis y Teleinformática (5° B)")
        self.stdout.write("  Lucía: LabProg 8 TEA, SistDig 9, Historia 7, Inglés 8, Análisis 6, Teleinfo 5")
        self.stdout.write("  Promedio parcial esperado: 7,2 · Inasistencias 1° cuat.: 7")
        self.stdout.write("  Asistencia: LabProg 84 % (aprueba) · Inglés 70 % (no acredita)")
        self.stdout.write("  Boletín anual: oculto (la preceptora lo publica con el interruptor del menú)")


    def _limpiar(self):
        """Borra lo que haya creado una corrida anterior (el comando es idempotente)."""
        User.objects.filter(username__in=USUARIOS_DEMO).delete()
        Materia.objects.filter(docente__dni__in=DNI_DOCENTES_DEMO).delete()
        Alumno.objects.filter(dni__in=DNI_ALUMNOS_DEMO).delete()
        BoletinConfig.objects.all().delete()
        PublicacionBoletin.objects.all().delete()

    def _alumno(self, curso, nombre, apellido, dni):
        return Alumno.objects.create(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            fecha_nacimiento=date(2008, 3, 15),
            anio=curso.anio,
            division=curso.division,
        )

    def _cat(self, materia, nombre, orden, grupo="", peso=None):
        return CategoriaEvaluacion.objects.create(
            nombre=nombre, materia=materia, orden=orden, grupo=grupo, peso=peso
        )

    def _nota(self, alumno, materia, categoria, valor, cuat=CUAT):
        return NotaEvaluacion.objects.create(
            alumno=alumno, materia=materia, categoria=categoria,
            cuatrimestre=cuat, valor=Decimal(str(valor)),
        )

    def _fechas_semanales(self, inicio, cantidad):
        """Devuelve 'cantidad' fechas, una por semana, desde 'inicio'."""
        return [inicio + timedelta(weeks=n) for n in range(cantidad)]

    def _cats_tp_eval(self, materia):
        """TP 1 y TP 2 (grupo Trabajos prácticos, 30 c/u) + Eval. 1 (grupo Evaluación, 40)."""
        tp1 = self._cat(materia, "TP 1", 1, "Trabajos prácticos", Decimal("30"))
        tp2 = self._cat(materia, "TP 2", 2, "Trabajos prácticos", Decimal("30"))
        ev1 = self._cat(materia, "Eval. 1", 3, "Evaluación", Decimal("40"))
        return tp1, tp2, ev1
