# -*- coding: utf-8 -*-
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
# date para fechas y timedelta para sumar semanas.
from datetime import date, timedelta
# Decimal para las notas.
from decimal import Decimal

# Tabla de usuarios de Django (login).
from django.contrib.auth.models import User
# Clase base de los comandos de manage.py.
from django.core.management.base import BaseCommand
from django.utils import timezone

# Tablas de otros modulos que el demo necesita llenar.
from alumnos.models import Alumno, Curso
from asistencia.models import RegistroAsistencia
from cuentas.models import Perfil
from docentes.models import Docente, Materia

# Tablas propias del modulo.
from calificaciones.models import (
    BoletinConfig,
    CategoriaEvaluacion,
    CierreCuatrimestre,
    ConfirmacionRite,
    NotaEvaluacion,
    PublicacionBoletin,
)

# Cuatrimestre por defecto de las notas del demo.
CUAT = 1
# Clave de todos los usuarios de prueba.
CLAVE = "prueba1234"

# DNI de los docentes y alumnos que crea el demo. Al limpiar se borra SOLO
# lo que tenga estos DNI, así nunca se tocan datos cargados por otros módulos.
# DNI de los 2 docentes del demo.
DNI_DOCENTES_DEMO = ["91000001", "91000009"]
# DNI de los 10 alumnos del demo (91000001 a 91000010).
DNI_ALUMNOS_DEMO = [f"910000{n:02d}" for n in range(1, 11)]
# "acosta.lucia" era el usuario viejo de la alumna: se borra por si quedó de antes.
# Usuarios que crea (y borra) el demo.
USUARIOS_DEMO = ["profesor1", "profesor2", "preceptora", "sebaema", "acosta.lucia"]


# Django busca una clase llamada Command: es lo que corre "python manage.py cargar_datos_demo".
class Command(BaseCommand):
    # Texto de ayuda del comando.
    help = "Carga los datos de demostración del módulo de calificaciones."

    # handle() es lo que se ejecuta al correr el comando.
    def handle(self, *args, **options):
        # Primero borra lo de una corrida anterior.
        self._limpiar()

        # ---- Cursos y docentes ----
        # Los cursos pueden existir porque los cargó el módulo Alumnos: se reutilizan.
        # Busca o crea los cursos 5° A y 5° B.
        cu5a, _ = Curso.objects.get_or_create(anio=5, division="A")
        cu5b, _ = Curso.objects.get_or_create(anio=5, division="B")

        # Cada docente tiene su propio usuario: ana es de las 3 materias de
        # programación y carlos de las 4 materias de la 5° B.
        # Crea o actualiza a la docente Ana.
        ana, _ = Docente.objects.update_or_create(
            dni="91000001",
            defaults={"nombre": "Ana", "apellido": "Martínez"},
        )
        # Crea o actualiza al docente Carlos.
        carlos, _ = Docente.objects.update_or_create(
            dni="91000009",
            defaults={"nombre": "Carlos", "apellido": "Russo"},
        )

        # ---- Materias ----
        # Crea las 7 materias, cada una con su curso y su docente.
        labprog = Materia.objects.create(nombre="Laboratorio de Programación", curso=cu5b, docente=ana)
        sistdig = Materia.objects.create(nombre="Sistemas digitales", curso=cu5b, docente=ana)
        labaplic = Materia.objects.create(nombre="Laboratorio de Aplicaciones", curso=cu5a, docente=ana)
        historia = Materia.objects.create(nombre="Historia", curso=cu5b, docente=carlos)
        ingles = Materia.objects.create(nombre="Inglés", curso=cu5b, docente=carlos)
        analisis = Materia.objects.create(nombre="Análisis Matemático", curso=cu5b, docente=carlos)
        teleinfo = Materia.objects.create(nombre="Teleinformática", curso=cu5b, docente=carlos)

        # ---- Alumnos ----
        # 5° B (los de la maqueta Cargar-notas)
        # Crea los 6 alumnos de 5° B (con el helper _alumno de abajo).
        lucia = self._alumno(cu5b, "Lucía", "Acosta", "91000001")
        tomas = self._alumno(cu5b, "Tomás", "Bravo", "91000002")
        nahuel = self._alumno(cu5b, "Nahuel", "Cáceres", "91000003")
        julieta = self._alumno(cu5b, "Julieta", "Domínguez", "91000004")
        mateo = self._alumno(cu5b, "Mateo", "Escobar", "91000005")
        camila = self._alumno(cu5b, "Camila", "Fernández", "91000006")
        # 5° A
        # Crea los 4 alumnos de 5° A.
        pedro = self._alumno(cu5a, "Pedro", "Gómez", "91000007")
        sofia = self._alumno(cu5a, "Sofía", "Herrera", "91000008")
        ramiro = self._alumno(cu5a, "Ramiro", "Ibáñez", "91000009")
        ana_j = self._alumno(cu5a, "Ana", "Juárez", "91000010")

        # ---- Categorías (estructura de la maqueta: TP 60 % + Evaluación 40 %) ----
        # Crea las 3 categorias con peso (TP 1, TP 2, Eval. 1) en las materias de Ana.
        tp1, tp2, ev1 = self._cats_tp_eval(labprog)
        sd_tp1, sd_tp2, sd_ev1 = self._cats_tp_eval(sistdig)
        la_tp1, la_tp2, la_ev1 = self._cats_tp_eval(labaplic)

        # Materias simples de otros docentes: una sola categoría
        # Las materias de Carlos tienen una sola categoria.
        cat_historia = self._cat(historia, "Calificación", 1)
        cat_ingles = self._cat(ingles, "Calificación", 1)
        cat_analisis = self._cat(analisis, "Calificación", 1)
        cat_teleinfo = self._cat(teleinfo, "Calificación", 1)

        # ---- Notas de Laboratorio de Programación (5° B) — igual a la maqueta ----
        # Notas de LabProg: para cada alumno, (TP 1, TP 2, Eval. 1).
        notas_labprog = {
            lucia: (8, 9, 8),      # calificación 8, TEA
            tomas: (5, 6, 4),      # calificación 5, TEP
            nahuel: (7, 7, 8),     # calificación 7, TEA
            julieta: (9, 10, 9),   # calificación 9, TEA
            mateo: (6, 5, 6),      # calificación 6, TEP
            camila: (10, 9, 10),   # calificación 10, TEA
        }
        # Recorre el diccionario y crea las 3 notas de cada alumno.
        for alumno, (n1, n2, n3) in notas_labprog.items():
            self._nota(alumno, labprog, tp1, n1)
            self._nota(alumno, labprog, tp2, n2)
            self._nota(alumno, labprog, ev1, n3)

        # Valoraciones preliminares elegidas por el docente (select de la planilla)
        # Valoracion elegida para cada alumno.
        valoraciones = {
            lucia: "TEA", tomas: "TEP", nahuel: "TEA",
            julieta: "TEA", mateo: "TEP", camila: "TEA",
        }
        # Crea el cierre del 1° cuatrimestre de cada alumno con su valoracion.
        for alumno, valoracion in valoraciones.items():
            CierreCuatrimestre.objects.create(
                alumno=alumno, materia=labprog, cuatrimestre=CUAT,
                valoracion_preliminar=valoracion,
                # C = cursa por primera vez, R = recursa (columna C/R de la planilla)
                # Nahuel recursa; el resto cursa por primera vez.
                cursada="R" if alumno is nahuel else "C",
            )

        # Bravo recuperó el 1° cuatrimestre con intensificación: quedó con 7
        # Marca que Tomas intensifico: tenia 5 y quedo con 7.
        CierreCuatrimestre.objects.filter(
            alumno=tomas, materia=labprog, cuatrimestre=CUAT,
        ).update(
            intensificacion=True, calificacion=Decimal("5"), calificacion_final=Decimal("7"),
        )

        # ---- 2° cuatrimestre de LabProg (columnas "2° CUATRIMESTRE" de la planilla) ----
        # Notas del 2° cuatrimestre: (TP 1, TP 2).
        notas_labprog_2c = {
            lucia: (9, 8),      # 9 · 8
            tomas: (7, 7),      # 7 · 7
            nahuel: (8, 7),     # 8 · 7
            julieta: (10, 9),   # 10 · 9
            mateo: (4, 5),      # 4 · 5
            # Camila todavía no tiene notas del 2° cuatrimestre
        }
        # Crea esas notas con cuat=2.
        for alumno, (n1, n2) in notas_labprog_2c.items():
            self._nota(alumno, labprog, tp1, n1, cuat=2)
            self._nota(alumno, labprog, tp2, n2, cuat=2)

        # Cierres del 2° cuatrimestre: valoración, calificación oficial y final del año
        # Cierres del 2° cuatrimestre: (valoracion, nota, final).
        cierres_2c = {
            lucia: ("TEA", "8", "8"),
            tomas: ("TEP", "7", "7"),
            nahuel: ("TEA", "7", "7"),
            julieta: ("TEA", "9", "9"),
            mateo: ("TED", "4", None),
        }
        # Los crea.
        for alumno, (valoracion, calif, final) in cierres_2c.items():
            CierreCuatrimestre.objects.create(
                alumno=alumno, materia=labprog, cuatrimestre=2,
                valoracion_preliminar=valoracion,
                calificacion=Decimal(calif),
                # Mateo no tiene final (None).
                calificacion_final=Decimal(final) if final else None,
            )

        # ---- Sistemas digitales (5° B): parcialmente cargada ----
        # Notas sueltas de Sistemas digitales (queda a medio cargar a proposito).
        self._nota(lucia, sistdig, sd_tp1, 9)
        self._nota(lucia, sistdig, sd_tp2, 9)
        self._nota(lucia, sistdig, sd_ev1, 9)
        self._nota(mateo, sistdig, sd_tp1, 6)
        self._nota(mateo, sistdig, sd_tp2, 7)
        self._nota(mateo, sistdig, sd_ev1, 6)

        # ---- Laboratorio de Aplicaciones (5° A): parcialmente cargada ----
        # Notas sueltas de Laboratorio de Aplicaciones.
        self._nota(pedro, labaplic, la_tp1, 8)
        self._nota(pedro, labaplic, la_tp2, 7)
        self._nota(pedro, labaplic, la_ev1, 9)
        self._nota(sofia, labaplic, la_tp1, 9)
        self._nota(sofia, labaplic, la_tp2, 9)
        self._nota(sofia, labaplic, la_ev1, 8)
        self._nota(ramiro, labaplic, la_tp1, 7)
        self._nota(ramiro, labaplic, la_ev1, 8)
        self._nota(ana_j, labaplic, la_ev1, 6)

        # ---- Notas de Lucía en el resto de las materias (igual a la maqueta) ----
        # Notas de Lucia en las materias de Carlos.
        self._nota(lucia, historia, cat_historia, 7)
        self._nota(lucia, ingles, cat_ingles, 8)
        self._nota(lucia, analisis, cat_analisis, 6)
        self._nota(lucia, teleinfo, cat_teleinfo, 5)

        # Teleinformática: no aprobó el 1° cuatrimestre y recuperó con intensificación
        # Lucia intensifico Teleinformatica: tenia 5 y quedo con 7.
        CierreCuatrimestre.objects.create(
            alumno=lucia, materia=teleinfo, cuatrimestre=CUAT,
            valoracion_preliminar="TEP", calificacion=Decimal("5"),
            intensificacion=True, calificacion_final=Decimal("7"),
        )
        # Su nota del 2° cuatrimestre...
        self._nota(lucia, teleinfo, cat_teleinfo, 7, cuat=2)
        # ...y el cierre del 2°.
        CierreCuatrimestre.objects.create(
            alumno=lucia, materia=teleinfo, cuatrimestre=2,
            valoracion_preliminar="TEP", calificacion=Decimal("7"),
        )

        # ---- Firmas del boletín: el adulto responsable y la estudiante tomó conocimiento ----
        # Firma del adulto responsable en el boletin de Lucia.
        ConfirmacionRite.objects.create(
            alumno=lucia, cuatrimestre=CUAT, tipo="adulto", usuario="seed",
        )
        # Firma de la estudiante.
        ConfirmacionRite.objects.create(
            alumno=lucia, cuatrimestre=CUAT, tipo="estudiante", usuario="sebaema",
        )

        # ---- Asistencias del ciclo ----
        # Se cargan clases semanales para todo 5° B. Así la regla del 80 % tiene
        # un denominador realista: Lucía falta 4 veces en LabProg (84 % anual,
        # aprueba) y 3 veces en Inglés (70 %, no acredita aunque tenga 8).
        # Alumnos de 5° B.
        alumnos_5b = [lucia, tomas, nahuel, julieta, mateo, camila]
        # Fechas en que Lucia falto a LabProg.
        faltas_lucia_labprog = {
            date(2026, 4, 14), date(2026, 5, 5),
            date(2026, 5, 26), date(2026, 6, 16),
        }
        # Fechas en que Lucia falto a Ingles.
        faltas_lucia_ingles = {
            date(2026, 3, 11), date(2026, 4, 8), date(2026, 4, 29),
        }

        # 16 clases en el 1° cuatrimestre y 10 en el 2° para LabProg.
        # Fechas de clase de LabProg: 16 semanas desde marzo y 10 desde agosto.
        fechas_labprog = (
            self._fechas_semanales(date(2026, 3, 3), 16)
            + self._fechas_semanales(date(2026, 8, 4), 10)
        )
        # Inglés: 10 clases en el 1° cuatrimestre.
        # Fechas de clase de Ingles.
        fechas_ingles = self._fechas_semanales(date(2026, 3, 4), 10)

        # Lista de registros de asistencia a crear.
        registros = []
        # Por cada clase de LabProg...
        for fecha in fechas_labprog:
            # ...y cada alumno...
            for alumno in alumnos_5b:
                # ...Ausente si es Lucia en una de sus faltas; si no, Presente.
                estado = "A" if alumno is lucia and fecha in faltas_lucia_labprog else "P"
                # Agrega el registro a la lista (todavia no lo guarda).
                registros.append(RegistroAsistencia(
                    alumno=alumno, materia=labprog, fecha=fecha, estado=estado,
                ))
        # Lo mismo para Ingles.
        for fecha in fechas_ingles:
            for alumno in alumnos_5b:
                estado = "A" if alumno is lucia and fecha in faltas_lucia_ingles else "P"
                registros.append(RegistroAsistencia(
                    alumno=alumno, materia=ingles, fecha=fecha, estado=estado,
                ))
        # bulk_create guarda todos los registros juntos (mas rapido).
        RegistroAsistencia.objects.bulk_create(registros)

        # ---- Boletín anual: arranca oculto para mostrar el interruptor en la expo ----
        # Deja el boletin del año oculto.
        PublicacionBoletin.objects.update_or_create(
            anio=timezone.now().year,
            defaults={"publicado": False, "fecha_publicacion": None, "usuario": ""},
        )

        # ---- Usuarios de prueba (uno por docente + el alumno) ----
        # Crea el usuario profesor1 (create_user guarda la clave encriptada).
        u_prof = User.objects.create_user("profesor1", password=CLAVE)
        u_prof.first_name = "Ana"
        u_prof.last_name = "Martínez"
        u_prof.save()
        # Le crea el perfil: rol docente, enlazado a la ficha de Ana.
        Perfil.objects.create(usuario=u_prof, rol=Perfil.DOCENTE, docente=ana)

        # Usuario profesor2, enlazado a Carlos.
        u_prof2 = User.objects.create_user("profesor2", password=CLAVE)
        u_prof2.first_name = "Carlos"
        u_prof2.last_name = "Russo"
        u_prof2.save()
        Perfil.objects.create(usuario=u_prof2, rol=Perfil.DOCENTE, docente=carlos)

        # Usuario preceptora con rol administrativo (secretaria).
        u_preceptora = User.objects.create_user("preceptora", password=CLAVE)
        u_preceptora.first_name = "Paula"
        u_preceptora.last_name = "Sosa"
        u_preceptora.save()
        Perfil.objects.create(usuario=u_preceptora, rol=Perfil.ADMINISTRATIVO)

        # Usuario sebaema con rol alumno, enlazado a Lucia.
        u_alum = User.objects.create_user("sebaema", password=CLAVE)
        u_alum.first_name = "Lucía"
        u_alum.save()
        Perfil.objects.create(usuario=u_alum, rol=Perfil.ALUMNO, alumno=lucia)

        # Mensajes que se ven en la consola al terminar.
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

    # ------------------------------------------------------------------
    #  helpers
    # ------------------------------------------------------------------

    # Borra lo que creo una corrida anterior.
    def _limpiar(self):
        """Borra lo que haya creado una corrida anterior (el comando es idempotente)."""
        # Borra los usuarios del demo.
        User.objects.filter(username__in=USUARIOS_DEMO).delete()
        # Las materias del demo son las de los docentes del demo (al borrarlas
        # se borran sus notas, categorías y asistencias).
        # Borra las materias de los docentes del demo.
        Materia.objects.filter(docente__dni__in=DNI_DOCENTES_DEMO).delete()
        # Borra los alumnos del demo.
        Alumno.objects.filter(dni__in=DNI_ALUMNOS_DEMO).delete()
        # Tablas propias del módulo: se reinician completas (BoletinConfig ya
        # no se usa, se limpia por si quedó de versiones anteriores).
        # Vacia las tablas de publicacion.
        BoletinConfig.objects.all().delete()
        PublicacionBoletin.objects.all().delete()

    # Helper: crea un alumno.
    def _alumno(self, curso, nombre, apellido, dni):
        # El módulo Alumnos guarda el año y la división en el alumno.
        # Lo crea con el año y la division del curso.
        return Alumno.objects.create(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            fecha_nacimiento=date(2008, 3, 15),
            anio=curso.anio,
            division=curso.division,
        )

    # Helper: crea una categoria.
    def _cat(self, materia, nombre, orden, grupo="", peso=None):
        return CategoriaEvaluacion.objects.create(
            nombre=nombre, materia=materia, orden=orden, grupo=grupo, peso=peso
        )

    # Helper: crea una nota.
    def _nota(self, alumno, materia, categoria, valor, cuat=CUAT):
        return NotaEvaluacion.objects.create(
            alumno=alumno, materia=materia, categoria=categoria,
            cuatrimestre=cuat, valor=Decimal(str(valor)),
        )

    # Helper: lista de fechas semanales.
    def _fechas_semanales(self, inicio, cantidad):
        """Devuelve 'cantidad' fechas, una por semana, desde 'inicio'."""
        # inicio + 0 semanas, + 1 semana, + 2...
        return [inicio + timedelta(weeks=n) for n in range(cantidad)]

    # Helper: crea las 3 categorias tipicas con sus grupos y pesos.
    def _cats_tp_eval(self, materia):
        """TP 1 y TP 2 (grupo Trabajos prácticos, 30 c/u) + Eval. 1 (grupo Evaluación, 40)."""
        tp1 = self._cat(materia, "TP 1", 1, "Trabajos prácticos", Decimal("30"))
        tp2 = self._cat(materia, "TP 2", 2, "Trabajos prácticos", Decimal("30"))
        ev1 = self._cat(materia, "Eval. 1", 3, "Evaluación", Decimal("40"))
        return tp1, tp2, ev1
