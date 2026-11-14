# -*- coding: utf-8 -*-
"""Tests de las pantallas del módulo de calificaciones.

Cubren los menú por rol, la carga de notas (guardado automático y ponderación),
la planilla del docente y el boletín del alumno.

Secciones:
- Menú por rol y "Mis notas" del alumno.
- Carga de notas y categorías.
- Planilla del docente (editable, TED, nota final, asistencia).
- Boletín (RITE) y firmas.
- Publicación anual del boletín.

    python manage.py test calificaciones
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from alumnos.models import Alumno, Curso
from asistencia.models import RegistroAsistencia
from calificaciones.models import (
    CategoriaEvaluacion,
    CierreCuatrimestre,
    ConfirmacionRite,
    NotaEvaluacion,
    PlanillaDatos,
    PublicacionBoletin,
)
from cuentas.models import Perfil
from docentes.models import Docente, Materia


# ─────────────────────────────────────────────
#  MENÚ POR ROL Y "MIS NOTAS"
# ─────────────────────────────────────────────

class MenuPorRolTests(TestCase):
    def setUp(self):
        self.curso = Curso.objects.create(anio=5, division="B")
        self.docente = Docente.objects.create(nombre="Ana", apellido="Prueba", dni="90000001")
        self.materia = Materia.objects.create(
            nombre="Laboratorio de Programación", curso=self.curso, docente=self.docente
        )
        self.materia_sin_cats = Materia.objects.create(
            nombre="Teleinformática", curso=self.curso, docente=self.docente
        )
        self.tp = CategoriaEvaluacion.objects.create(
            nombre="TP 1", materia=self.materia, orden=1,
            grupo="Trabajos prácticos", peso=Decimal("50"),
        )
        self.eval = CategoriaEvaluacion.objects.create(
            nombre="Eval. 1", materia=self.materia, orden=2,
            grupo="Evaluación", peso=Decimal("50"),
        )

        self.alumno = Alumno.objects.create(
            nombre="Lucía", apellido="Acosta", dni="90000002",
            fecha_nacimiento=date(2008, 5, 1), anio=self.curso.anio, division=self.curso.division,
        )
        self.alumno2 = Alumno.objects.create(
            nombre="Tomás", apellido="Bravo", dni="90000003",
            fecha_nacimiento=date(2008, 6, 2), anio=self.curso.anio, division=self.curso.division,
        )

        # 3 de 4 celdas con nota => 75% cargado
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.tp, cuatrimestre=1, valor=Decimal("8"))
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.eval, cuatrimestre=1, valor=Decimal("9"))
        NotaEvaluacion.objects.create(alumno=self.alumno2, materia=self.materia,
                                       categoria=self.tp, cuatrimestre=1, valor=Decimal("5"))

        # inasistencias del alumno: 2 ausentes + 1 tardanza => 2,5.
        # Se agregan 10 presentes para que la asistencia supere el 80 %.
        RegistroAsistencia.objects.create(alumno=self.alumno, materia=self.materia,
                                          fecha=date(2026, 4, 10), estado="A")
        RegistroAsistencia.objects.create(alumno=self.alumno, materia=self.materia,
                                          fecha=date(2026, 4, 17), estado="A")
        RegistroAsistencia.objects.create(alumno=self.alumno, materia=self.materia,
                                          fecha=date(2026, 4, 24), estado="T")
        for dia in (1, 2, 3, 7, 8, 9, 14, 15, 21, 22):
            RegistroAsistencia.objects.create(
                alumno=self.alumno, materia=self.materia,
                fecha=date(2026, 4, dia), estado="P",
            )

        self.u_docente = User.objects.create_user("docente1", password="clave123")
        Perfil.objects.create(usuario=self.u_docente, rol=Perfil.DOCENTE, docente=self.docente)
        self.u_alumno = User.objects.create_user("alumno1", password="clave123")
        Perfil.objects.create(usuario=self.u_alumno, rol=Perfil.ALUMNO, alumno=self.alumno)
        self.u_admin = User.objects.create_user("admin1", password="clave123")
        Perfil.objects.create(usuario=self.u_admin, rol=Perfil.ADMINISTRATIVO)

    # ---------------- menú del docente ----------------

    def test_menu_docente(self):
        c = Client()
        c.force_login(self.u_docente)
        r = c.get("/calificaciones/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "calificaciones/menu_docente.html")
        for texto in ("Mis materias", "Materias a cargo", "Laboratorio de Programación",
                      "Notas cargadas: 75%", "Cargar notas", "Ver planilla",
                      "Materias con el 1° cuatrimestre cerrado", "1° cuat. abierto"):
            self.assertContains(r, texto)
        # barra superior y footer compartidos con el resto de los módulos
        self.assertContains(r, 'class="logo"')
        self.assertContains(r, "Inicio")
        self.assertContains(r, "Comunicados")
        self.assertContains(r, 'class="footer-titulo"')

    def test_menu_docente_materia_sin_categorias(self):
        c = Client()
        c.force_login(self.u_docente)
        r = c.get("/calificaciones/")
        self.assertContains(r, "Teleinformática")
        self.assertContains(r, "Creá categorías para poder cargar notas")

    def test_menu_docente_cuat_2(self):
        c = Client()
        c.force_login(self.u_docente)
        r = c.get("/calificaciones/?cuat=2")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "2° cuat. abierto")

    # ---------------- menú del alumno ----------------

    def test_menu_alumno(self):
        c = Client()
        c.force_login(self.u_alumno)
        r = c.get("/calificaciones/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "calificaciones/menu_alumno.html")
        for texto in ("Mis notas", "Val. preliminar", "Mi boletín", "Inasistencias",
                      "Aprobada", "TEA", "Acosta, Lucía"):
            self.assertContains(r, texto)
        # el texto viejo del módulo Asistencia ya no se muestra en la tarjeta
        self.assertNotContains(r, "se lee del módulo Asistencia")
        # calificación ponderada de Lucía: (8*50 + 9*50) / 100 = 8,5 -> 9
        self.assertContains(r, '<td class="fuerte">9</td>')
        # inasistencias: 2,5 con coma (formato es-AR)
        self.assertContains(r, "2,5")

    def test_menu_alumno_muestra_ted_en_rojo(self):
        """TED (0-4) se muestra en rojo también en Mis notas."""
        NotaEvaluacion.objects.filter(
            alumno=self.alumno, materia=self.materia, cuatrimestre=1,
        ).update(valor=Decimal("4"))
        c = Client()
        c.force_login(self.u_alumno)
        r = c.get("/calificaciones/")
        self.assertContains(r, '<span class="ted">TED</span>')

    def test_asistencia_insuficiente_no_aprueba_la_materia(self):
        """Con menos del 80 % de asistencia la materia no queda aprobada."""
        for dia in (1, 2):
            RegistroAsistencia.objects.create(
                alumno=self.alumno, materia=self.materia,
                fecha=date(2026, 5, dia), estado="A",
            )
        c = Client()
        c.force_login(self.u_alumno)
        r = c.get("/calificaciones/")
        self.assertContains(r, "No acredita por asistencia")

    def test_menu_alumno_no_ve_cargas_del_docente(self):
        c = Client()
        c.force_login(self.u_alumno)
        r = c.get("/calificaciones/")
        self.assertNotContains(r, "Cargar notas")
        self.assertNotContains(r, "Materias a cargo")

    # ---------------- menú de la secretaría ----------------

    def test_menu_administrativo_fallback(self):
        """La secretaría ve las planillas de todos los docentes y el buscador de boletines."""
        c = Client()
        c.force_login(self.u_admin)
        r = c.get("/calificaciones/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "calificaciones/menu.html")
        self.assertContains(r, "Planillas de calificaciones")
        self.assertContains(r, "Boletín de un alumno")
        self.assertContains(r, "Ana Prueba")   # el docente de la materia
        self.assertContains(r, "Laboratorio de Programación")
        self.assertNotContains(r, "Cargar notas")


# ─────────────────────────────────────────────
#  CARGA DE NOTAS Y CATEGORÍAS
# ─────────────────────────────────────────────

class CargarNotasTests(TestCase):
    def setUp(self):
        self.curso = Curso.objects.create(anio=5, division="B")
        self.docente = Docente.objects.create(nombre="Ana", apellido="Prueba", dni="90000011")
        self.materia = Materia.objects.create(
            nombre="Laboratorio de Programación", curso=self.curso, docente=self.docente
        )
        self.tp = CategoriaEvaluacion.objects.create(
            nombre="TP 1", materia=self.materia, orden=1,
            grupo="Trabajos prácticos", peso=Decimal("30"),
        )
        self.tp2 = CategoriaEvaluacion.objects.create(
            nombre="TP 2", materia=self.materia, orden=2,
            grupo="Trabajos prácticos", peso=Decimal("30"),
        )
        self.eval = CategoriaEvaluacion.objects.create(
            nombre="Eval. 1", materia=self.materia, orden=3,
            grupo="Evaluación", peso=Decimal("40"),
        )
        self.alumno = Alumno.objects.create(
            nombre="Lucía", apellido="Acosta", dni="90000012",
            fecha_nacimiento=date(2008, 5, 1), anio=self.curso.anio, division=self.curso.division,
        )
        # igual a la maqueta: (8*30 + 9*30 + 8*40) / 100 = 8,3 -> 8
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.tp, cuatrimestre=1, valor=Decimal("8"))
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.tp2, cuatrimestre=1, valor=Decimal("9"))
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.eval, cuatrimestre=1, valor=Decimal("8"))

        self.u_docente = User.objects.create_user("docente2", password="clave123")
        Perfil.objects.create(usuario=self.u_docente, rol=Perfil.DOCENTE, docente=self.docente)

    def _login(self):
        self.client.force_login(self.u_docente)

    def test_pantalla_cargar_notas(self):
        self._login()
        url = reverse("profesor_cargar_notas", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "calificaciones/cargar_notas.html")
        for texto in ("Guardado automático", "Categorías", "Importar Excel", "Ver planilla",
                      "Trabajos prácticos · 60 %",
                      "Evaluación · 40 %",
                      "Val. preliminar", "Calificación", "Estado",
                      "Acosta, Lucía", "Aprobada"):
            self.assertContains(r, texto)
        # calificación calculada en gris: 8
        self.assertContains(r, 'calif-fila">8</td>')
        # data-peso / data-peso-grupo con punto decimal (los lee parseFloat en JS)
        self.assertContains(r, 'data-peso="30"')
        self.assertContains(r, 'data-peso-grupo="60"')
        # valor del input limpio ("8", no "8,00" ni "8.0")
        self.assertContains(r, 'value="8"')
        # select de valoración con las 3 opciones
        self.assertContains(r, ">TEA</option>")
        self.assertContains(r, ">TEP</option>")
        self.assertContains(r, ">TED</option>")

    def test_aviso_si_falta_la_libreria_de_excel(self):
        """Sin openpyxl, la pantalla de Excel avisa qué instalar en vez de fallar."""
        from calificaciones import views
        self._login()
        url = reverse("profesor_cargar_excel", kwargs={"cuat": 1, "materia_id": self.materia.id})
        original = views.EXCEL_DISPONIBLE
        try:
            views.EXCEL_DISPONIBLE = False
            self.assertContains(self.client.get(url), "Falta instalar la librería de Excel")
            views.EXCEL_DISPONIBLE = True
            self.assertNotContains(self.client.get(url), "Falta instalar la librería de Excel")
        finally:
            views.EXCEL_DISPONIBLE = original

    def test_guardar_nota_devuelve_calificacion_ponderada(self):
        self._login()
        url = reverse("profesor_guardar_nota", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.post(url, {
            "alumno_id": self.alumno.id,
            "cat_id": self.eval.id,
            "valor": "10",
        })
        data = r.json()
        self.assertTrue(data["ok"])
        # (8*30 + 9*30 + 10*40) / 100 = 8,7 -> 9
        self.assertEqual(data["calificacion"], "9")
        self.assertEqual(data["estado_materia"], "Aprobada")

    def test_guardar_nota_acepta_coma_decimal(self):
        """En es-AR el docente escribe 7,5 y el sistema lo guarda como 7.5."""
        self._login()
        url = reverse("profesor_guardar_nota", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.post(url, {
            "alumno_id": self.alumno.id,
            "cat_id": self.eval.id,
            "valor": "7,5",
        })
        self.assertTrue(r.json()["ok"])
        nota = NotaEvaluacion.objects.get(
            alumno=self.alumno, materia=self.materia,
            categoria=self.eval, cuatrimestre=1,
        )
        self.assertEqual(nota.valor, Decimal("7.5"))

    def test_las_inasistencias_no_se_editan_en_cargar_notas(self):
        """Las inasistencias salen del módulo Asistencia: la grilla solo las muestra."""
        self._login()
        url = reverse("profesor_cargar_notas", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.get(url)
        self.assertContains(r, 'class="n nota"', count=3)
        self.assertNotContains(r, 'class="n inasistencia"')
        self.assertNotContains(r, "guardar-inasistencia")

    def test_volver_de_categorias_y_excel_lleva_a_cargar_notas(self):
        """'Volver a <materia>' vuelve a Cargar notas, no a la planilla."""
        self._login()
        kwargs = {"cuat": 1, "materia_id": self.materia.id}
        url_cargar = reverse("profesor_cargar_notas", kwargs=kwargs)
        url_planilla = reverse("profesor_planilla", kwargs=kwargs)
        for vista in ("profesor_categorias", "profesor_cargar_excel"):
            with self.subTest(vista=vista):
                r = self.client.get(reverse(vista, kwargs=kwargs))
                self.assertContains(r, f'href="{url_cargar}">← Volver a Laboratorio de Programación</a>')
                self.assertNotContains(r, url_planilla)

    def test_eliminar_categoria_solo_por_post(self):
        self._login()
        url = reverse("profesor_eliminar_categoria",
                      kwargs={"cuat": 1, "materia_id": self.materia.id, "cat_id": self.tp.id})
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(CategoriaEvaluacion.objects.filter(id=self.tp.id).exists())
        self.client.post(url)
        self.assertFalse(CategoriaEvaluacion.objects.filter(id=self.tp.id).exists())

    def test_confirmar_excel_acepta_coma_decimal(self):
        """Las notas del Excel con coma ('6,5') se guardan bien."""
        self._login()
        sesion = self.client.session
        sesion[f"excel_1_{self.materia.id}"] = [
            {"alumno_id": self.alumno.id,
             "notas": {str(self.tp.id): "6,5", str(self.tp2.id): "abc"}},
        ]
        sesion.save()
        kwargs = {"cuat": 1, "materia_id": self.materia.id}
        r = self.client.post(reverse("profesor_confirmar_excel", kwargs=kwargs))
        self.assertRedirects(r, reverse("profesor_cargar_notas", kwargs=kwargs),
                             fetch_redirect_response=False)
        nota = NotaEvaluacion.objects.get(alumno=self.alumno, categoria=self.tp, cuatrimestre=1)
        self.assertEqual(nota.valor, Decimal("6.5"))
        # un valor que no es nota no pisa la nota que ya estaba
        nota2 = NotaEvaluacion.objects.get(alumno=self.alumno, categoria=self.tp2, cuatrimestre=1)
        self.assertEqual(nota2.valor, Decimal("9"))

    def test_cargar_notas_muestra_inasistencias_de_asistencia(self):
        """Las inasistencias se leen del módulo Asistencia (ausente 1, tardanza 0,5)."""
        RegistroAsistencia.objects.create(
            alumno=self.alumno, materia=self.materia,
            fecha=date(2026, 4, 10), estado="A",
        )
        RegistroAsistencia.objects.create(
            alumno=self.alumno, materia=self.materia,
            fecha=date(2026, 4, 17), estado="A",
        )
        RegistroAsistencia.objects.create(
            alumno=self.alumno, materia=self.materia,
            fecha=date(2026, 4, 24), estado="T",
        )
        self._login()
        url = reverse("profesor_cargar_notas", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.get(url)
        self.assertContains(r, '<td class="c">2,5</td>')

    def test_cargar_notas_avisa_asistencia_insuficiente(self):
        """Con una sola clase y una falta, la materia no se acredita."""
        RegistroAsistencia.objects.create(
            alumno=self.alumno, materia=self.materia,
            fecha=date(2026, 4, 10), estado="A",
        )
        self._login()
        url = reverse("profesor_cargar_notas", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.get(url)
        self.assertContains(r, "No acredita por asistencia")

    def test_guardar_valoracion(self):
        self._login()
        url = reverse("profesor_guardar_valoracion", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.post(url, {"alumno_id": self.alumno.id, "valoracion": "TEP"})
        self.assertTrue(r.json()["ok"])

        cierre = CierreCuatrimestre.objects.get(
            alumno=self.alumno, materia=self.materia, cuatrimestre=1
        )
        self.assertEqual(cierre.valoracion_preliminar, "TEP")

        # cambiar de nuevo sobreescribe el mismo cierre
        r = self.client.post(url, {"alumno_id": self.alumno.id, "valoracion": "TEA"})
        self.assertTrue(r.json()["ok"])
        self.assertEqual(CierreCuatrimestre.objects.filter(
            alumno=self.alumno, materia=self.materia, cuatrimestre=1).count(), 1)
        cierre.refresh_from_db()
        self.assertEqual(cierre.valoracion_preliminar, "TEA")

    def test_guardar_valoracion_invalida(self):
        self._login()
        url = reverse("profesor_guardar_valoracion", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.post(url, {"alumno_id": self.alumno.id, "valoracion": "XXX"})
        self.assertEqual(r.status_code, 400)

    def test_guardar_con_ids_que_no_son_numeros_no_rompe(self):
        """Un alumno_id o cat_id inválido responde 404 en vez de un error del servidor."""
        self._login()
        url = reverse("profesor_guardar_nota", kwargs={"cuat": 1, "materia_id": self.materia.id})
        r = self.client.post(url, {"alumno_id": "abc", "cat_id": self.eval.id, "valor": "8"})
        self.assertEqual(r.status_code, 404)
        r = self.client.post(url, {"alumno_id": self.alumno.id, "cat_id": "abc", "valor": "8"})
        self.assertEqual(r.status_code, 404)
        # la nota que ya estaba no se tocó
        nota = NotaEvaluacion.objects.get(alumno=self.alumno, categoria=self.eval, cuatrimestre=1)
        self.assertEqual(nota.valor, Decimal("8"))


# ─────────────────────────────────────────────
#  PLANILLA DEL DOCENTE
# ─────────────────────────────────────────────

class PlanillaDocenteTests(TestCase):
    """Planilla del docente (maqueta Main): los dos cuatrimestres + cierre."""

    def setUp(self):
        self.curso = Curso.objects.create(anio=5, division="B")
        self.docente = Docente.objects.create(nombre="Ana", apellido="Prueba", dni="90000021")
        self.materia = Materia.objects.create(
            nombre="Laboratorio de Programación", curso=self.curso, docente=self.docente
        )
        self.tp = CategoriaEvaluacion.objects.create(
            nombre="TP 1", materia=self.materia, orden=1,
            grupo="Trabajos prácticos", peso=Decimal("30"),
        )
        self.tp2 = CategoriaEvaluacion.objects.create(
            nombre="TP 2", materia=self.materia, orden=2,
            grupo="Trabajos prácticos", peso=Decimal("30"),
        )
        self.alumno = Alumno.objects.create(
            nombre="Lucía", apellido="Acosta", dni="90000022",
            fecha_nacimiento=date(2008, 5, 1), anio=self.curso.anio, division=self.curso.division,
        )
        # 1° cuatrimestre: 8 y 9 ; 2° cuatrimestre: 9
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.tp, cuatrimestre=1, valor=Decimal("8"))
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.tp2, cuatrimestre=1, valor=Decimal("9"))
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.tp, cuatrimestre=2, valor=Decimal("9"))
        # 1 falta y 4 presentes: 80 % justo, así la materia se puede aprobar.
        RegistroAsistencia.objects.create(alumno=self.alumno, materia=self.materia,
                                          fecha=date(2026, 4, 10), estado="A")
        for dia in (11, 12, 13, 14):
            RegistroAsistencia.objects.create(
                alumno=self.alumno, materia=self.materia,
                fecha=date(2026, 4, dia), estado="P",
            )

        self.u_docente = User.objects.create_user("docente3", password="clave123")
        Perfil.objects.create(usuario=self.u_docente, rol=Perfil.DOCENTE, docente=self.docente)

    def _url(self, cuat=1):
        return reverse("profesor_planilla",
                       kwargs={"cuat": cuat, "materia_id": self.materia.id})

    def test_planilla_se_ve(self):
        """La planilla es la hoja imprimible de oficio vertical (maqueta planilla-docente)."""
        self.client.force_login(self.u_docente)
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "calificaciones/planilla.html")
        for texto in ("PLANILLA DE CALIFICACIONES",
                      "ESCUELA DE EDUCACIÓN SECUNDARIA:",
                      "EEST N°3",
                      "MATERIA:",
                      "PROFESOR/A:",
                      "AÑO:", "SECCIÓN:", "TURNO:", "PRECEPTOR/A:",
                      "N° DE ORDEN",
                      "APELLIDO/S Y NOMBRE/S",
                      "CURSA", "RECURSA", "(C/R)",
                      "1° CUATRIMESTRE", "2° CUATRIMESTRE", "INTENSIFICACIÓN",
                      "CALIFICACIÓN FINAL",
                      "CALIFICACIONES/", "VALORACIÓN PRELIMINAR",
                      "CALIFICACIÓN 1° CUATRIMESTRE", "INASISTENCIAS DEL 1° CUATRIMESTRE",
                      "CALIFICACIÓN 2° CUATRIMESTRE", "INTENSIFICACIÓN 1° CUATRIMESTRE",
                      "INASISTENCIAS DEL 2° CUATRIMESTRE",
                      "DICIEMBRE", "FEBRERO",
                      "TOTAL DE ESTUDIANTES", "APROBADAS/OS", "DESAPROBADAS/OS", "SIN EVALUAR",
                      "TOTAL DE CLASES DE LA MATERIA", "CLASES EFECTIVAMENTE DADAS",
                      "IMPORTANTE: LEER LAS SIGUIENTES CONSIDERACIONES",
                      "FIRMA",
                      "Guardar cambios", "Cerrar 1° cuatrimestre",
                      "Imprimir (oficio vertical)",
                      "ACOSTA Lucía"):
            self.assertContains(r, texto)
        # las notas van en columnas sueltas (una por categoría)
        self.assertContains(r, '<td class="n">8</td>')
        self.assertContains(r, '<td class="n">9</td>')

    def test_totales_de_la_hoja(self):
        self.client.force_login(self.u_docente)
        r = self.client.get(self._url())
        self.assertContains(r, '<th class="r">TOTAL DE ESTUDIANTES</th><td>1</td><td>1</td><td>1</td>')
        self.assertContains(r, '<th class="r">APROBADAS/OS</th><td>1</td><td>1</td>')
        self.assertContains(r, '<th class="r">SIN EVALUAR</th><td>0</td><td>0</td>')

    def test_guardar_cursada_y_dic(self):
        self.client.force_login(self.u_docente)
        r = self.client.post(self._url(), {
            "accion": "guardar",
            f"cursada_{self.alumno.id}": "R",
            f"dic_{self.alumno.id}": "7",
            f"feb_{self.alumno.id}": "",
        })
        self.assertEqual(r.status_code, 302)
        cierre = CierreCuatrimestre.objects.get(
            alumno=self.alumno, materia=self.materia, cuatrimestre=1
        )
        self.assertEqual(cierre.cursada, "R")
        self.assertEqual(cierre.nota_diciembre, Decimal("7"))

    def test_guardar_turno_y_preceptora(self):
        self.client.force_login(self.u_docente)
        r = self.client.post(self._url(), {
            "accion": "guardar",
            "turno": "Mañana",
            "preceptor": "Laura Gómez",
        })
        self.assertEqual(r.status_code, 302)
        datos = PlanillaDatos.objects.get(materia=self.materia)
        self.assertEqual(datos.turno, "Mañana")
        self.assertEqual(datos.preceptor, "Laura Gómez")
        r = self.client.get(self._url())
        self.assertContains(r, 'value="Mañana"')
        self.assertContains(r, 'value="Laura Gómez"')

    def test_cerrar_cuatrimestre(self):
        self.client.force_login(self.u_docente)
        r = self.client.post(self._url(), {"accion": "cerrar"})
        self.assertEqual(r.status_code, 302)
        cierre = CierreCuatrimestre.objects.get(
            alumno=self.alumno, materia=self.materia, cuatrimestre=1
        )
        self.assertTrue(cierre.cerrado)
        self.assertIsNotNone(cierre.fecha_cierre)
        # la calificación oficial queda fija con lo cargado
        self.assertEqual(cierre.calificacion, Decimal("9"))
        # la planilla muestra la fecha y el botón para reabrir
        r = self.client.get(self._url())
        self.assertContains(r, "cuatrimestre cerrado el")
        self.assertContains(r, "Reabrir 1° cuatrimestre")
        self.assertNotContains(r, "Cerrar 1° cuatrimestre")

    def test_cuatrimestre_cerrado_bloquea_las_notas(self):
        """Con el cuatrimestre cerrado la grilla es de solo lectura y no se guardan notas."""
        self.client.force_login(self.u_docente)
        self.client.post(self._url(), {"accion": "cerrar"})
        kwargs = {"cuat": 1, "materia_id": self.materia.id}

        r = self.client.get(reverse("profesor_cargar_notas", kwargs=kwargs))
        self.assertContains(r, "está cerrado")
        self.assertContains(r, "readonly")

        r = self.client.post(reverse("profesor_guardar_nota", kwargs=kwargs),
                             {"alumno_id": self.alumno.id, "cat_id": self.tp.id, "valor": "2"})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(NotaEvaluacion.objects.get(categoria=self.tp, cuatrimestre=1).valor, Decimal("8"))

        # el 2° cuatrimestre sigue abierto
        r = self.client.post(reverse("profesor_guardar_nota", kwargs={"cuat": 2, "materia_id": self.materia.id}),
                             {"alumno_id": self.alumno.id, "cat_id": self.tp2.id, "valor": "7"})
        self.assertEqual(r.status_code, 200)

    def test_reabrir_libera_las_notas(self):
        self.client.force_login(self.u_docente)
        self.client.post(self._url(), {"accion": "cerrar"})
        self.client.post(self._url(), {"accion": "reabrir"})
        cierre = CierreCuatrimestre.objects.get(alumno=self.alumno, materia=self.materia, cuatrimestre=1)
        self.assertFalse(cierre.cerrado)
        self.assertIsNone(cierre.calificacion)
        self.assertIsNone(cierre.fecha_cierre)
        r = self.client.post(reverse("profesor_guardar_nota", kwargs={"cuat": 1, "materia_id": self.materia.id}),
                             {"alumno_id": self.alumno.id, "cat_id": self.tp.id, "valor": "2"})
        self.assertEqual(r.status_code, 200)

    def test_cada_materia_tiene_su_fecha_de_cierre(self):
        """Cerrar una materia no marca como cerradas a las demás."""
        otra = Materia.objects.create(nombre="Sistemas digitales", curso=self.curso, docente=self.docente)
        self.client.force_login(self.u_docente)
        self.client.post(self._url(), {"accion": "cerrar"})
        r = self.client.get(reverse("calificaciones_menu"))
        materias = {m["id"]: m for m in r.context["materias"]}
        self.assertIsNotNone(materias[self.materia.id]["fecha_cierre"])
        self.assertIsNone(materias[otra.id]["fecha_cierre"])
        self.assertEqual(r.context["cerradas"], 1)

    def test_no_se_borra_una_categoria_con_notas_cerradas(self):
        self.client.force_login(self.u_docente)
        self.client.post(self._url(), {"accion": "cerrar"})
        url = reverse("profesor_eliminar_categoria",
                      kwargs={"cuat": 2, "materia_id": self.materia.id, "cat_id": self.tp.id})
        r = self.client.post(url, follow=True)
        self.assertContains(r, "tiene notas de un cuatrimestre cerrado")
        self.assertTrue(CategoriaEvaluacion.objects.filter(id=self.tp.id).exists())

    def test_cargar_intensificacion(self):
        """La intensificación se guarda solo si el 1° no estaba aprobado y es 7 o más."""
        NotaEvaluacion.objects.filter(cuatrimestre=1).update(valor=Decimal("4"))
        self.client.force_login(self.u_docente)
        r = self.client.post(self._url(), {"accion": "guardar", f"intens_{self.alumno.id}": "5"}, follow=True)
        self.assertContains(r, "la intensificación tiene que ser una nota de 7 a 10")
        self.client.post(self._url(), {"accion": "guardar", f"intens_{self.alumno.id}": "8"})
        cierre1 = CierreCuatrimestre.objects.get(alumno=self.alumno, materia=self.materia, cuatrimestre=1)
        self.assertTrue(cierre1.intensificacion)
        self.assertEqual(cierre1.calificacion_final, Decimal("8"))
        # la final usa la intensificación: (8 + 9) / 2 = 8,5 -> 9
        r = self.client.get(self._url())
        self.assertEqual(r.context["filas"][0]["intensificacion"], "8")
        self.assertEqual(r.context["filas"][0]["final"], "9")
        # vaciar la casilla la borra
        self.client.post(self._url(), {"accion": "guardar", f"intens_{self.alumno.id}": ""})
        cierre1.refresh_from_db()
        self.assertFalse(cierre1.intensificacion)

    def test_no_intensifica_quien_aprobo_el_primer_cuatrimestre(self):
        self.client.force_login(self.u_docente)
        r = self.client.post(self._url(), {"accion": "guardar", f"intens_{self.alumno.id}": "8"}, follow=True)
        self.assertContains(r, "no necesita intensificación")
        self.assertFalse(CierreCuatrimestre.objects.get(
            alumno=self.alumno, materia=self.materia, cuatrimestre=1).intensificacion)

    def test_nota_final_a_mano(self):
        """Si el docente deja la final automática no se guarda; si la cambia, queda la suya."""
        self.client.force_login(self.u_docente)
        self.client.post(self._url(), {"accion": "guardar", f"final_{self.alumno.id}": "9"})
        cierre2 = CierreCuatrimestre.objects.get(alumno=self.alumno, materia=self.materia, cuatrimestre=2)
        self.assertIsNone(cierre2.calificacion_final)  # 9 es la automática

        self.client.post(self._url(), {"accion": "guardar", f"final_{self.alumno.id}": "10"})
        cierre2.refresh_from_db()
        self.assertEqual(cierre2.calificacion_final, Decimal("10"))
        self.assertEqual(self.client.get(self._url()).context["filas"][0]["final"], "10")

        # vaciarla vuelve a la automática
        self.client.post(self._url(), {"accion": "guardar", f"final_{self.alumno.id}": ""})
        self.assertEqual(self.client.get(self._url()).context["filas"][0]["final"], "9")

    def test_la_planilla_muestra_las_inasistencias_de_asistencia(self):
        """Las inasistencias se leen del módulo Asistencia y no se editan en la planilla."""
        # El setUp ya cargó 1 ausente en abril; se suma una tardanza (media falta).
        RegistroAsistencia.objects.create(
            alumno=self.alumno, materia=self.materia,
            fecha=date(2026, 5, 8), estado="T",
        )
        self.client.force_login(self.u_docente)
        r = self.client.get(self._url())
        fila = next(f for f in r.context["filas"] if f["id"] == self.alumno.id)
        self.assertEqual(fila["inas1"], "1,5")
        self.assertNotContains(r, f'name="inas1_{self.alumno.id}"')

    def test_nota_final_automatica_con_los_dos_cuatrimestres(self):
        """La final aparece sola cuando ambos cuatrimestres tienen nota."""
        self.client.force_login(self.u_docente)
        r = self.client.get(self._url())
        # 1° cuatrimestre: (8+9)/2 = 8,5 -> 9 · 2°: 9 => final (9+9)/2 = 9
        self.assertEqual(r.context["filas"][0]["final"], "9")

        # sin notas del 2° cuatrimestre no hay nota final
        NotaEvaluacion.objects.filter(cuatrimestre=2).delete()
        r = self.client.get(self._url())
        self.assertEqual(r.context["filas"][0]["final"], "")

    def test_asistencia_baja_no_aprueba_ni_muestra_final_aprobada(self):
        """Con 60 % de asistencia la materia no se acredita."""
        RegistroAsistencia.objects.create(
            alumno=self.alumno, materia=self.materia,
            fecha=date(2026, 4, 15), estado="A",
        )
        self.client.force_login(self.u_docente)
        r = self.client.get(self._url())
        fila = r.context["filas"][0]
        self.assertTrue(fila["no_acredita"])
        self.assertFalse(fila["d1"]["aprobada"])
        self.assertFalse(fila["final_aprobada"])
        # la final se sigue viendo, pero en rojo y con la aclaración
        self.assertContains(r, 'class="ll no-acredita"')
        self.assertContains(r, 'title="Asistencia menor al 80 %: no acredita la materia"')

    def test_planilla_muestra_ted_en_negro(self):
        """En la planilla oficial TED no va en rojo (sí en Mis notas y en el boletín)."""
        NotaEvaluacion.objects.filter(cuatrimestre=1).update(valor=Decimal("4"))
        self.client.force_login(self.u_docente)
        r = self.client.get(self._url())
        self.assertContains(r, '<td class="n">TED</td>')
        self.assertNotContains(r, 'class="ted"')

    def test_url_de_la_planilla(self):
        """La planilla se llama planilla-calificaciones y usa el id de la materia."""
        self.assertEqual(
            self._url(),
            f"/calificaciones/profesor/1/{self.materia.id}/planilla-calificaciones/",
        )

    def test_planilla_tiene_celdas_editables_y_filas_en_blanco(self):
        """El docente puede corregir n°/nombre y completar las filas vacías."""
        self.client.force_login(self.u_docente)
        r = self.client.get(self._url())
        self.assertContains(r, 'value="ACOSTA Lucía"')
        self.assertContains(r, 'aria-label="Renglón 2 — apellido y nombre"')
        self.assertContains(r, 'aria-label="Renglón 2 — inasistencias 1° cuatrimestre"')


# ─────────────────────────────────────────────
#  PLANILLA SEGÚN EL USUARIO
# ─────────────────────────────────────────────

class PlanillaPorUsuarioTests(TestCase):
    """Cada docente ve solo sus materias; la secretaría ve todas.

    - El docente solo puede abrir la planilla de sus materias.
    - La secretaría (preceptora) puede abrir las de todos, para imprimir, y en
      cada planilla figura el nombre del docente de esa materia.
    """

    def setUp(self):
        self.curso = Curso.objects.create(anio=5, division="B")
        self.ana = Docente.objects.create(nombre="Ana", apellido="Martínez", dni="90000041")
        self.carlos = Docente.objects.create(nombre="Carlos", apellido="Russo", dni="90000042")
        self.materia_ana = Materia.objects.create(
            nombre="Laboratorio de Programación", curso=self.curso, docente=self.ana
        )
        self.materia_carlos = Materia.objects.create(
            nombre="Historia", curso=self.curso, docente=self.carlos
        )
        CategoriaEvaluacion.objects.create(
            nombre="TP 1", materia=self.materia_ana, orden=1, peso=Decimal("100"),
        )
        CategoriaEvaluacion.objects.create(
            nombre="Calificación", materia=self.materia_carlos, orden=1, peso=Decimal("100"),
        )

        self.u_ana = User.objects.create_user("profesor1", password="clave123")
        self.u_ana.first_name = "Ana"
        self.u_ana.last_name = "Martínez"
        self.u_ana.save()
        Perfil.objects.create(usuario=self.u_ana, rol=Perfil.DOCENTE, docente=self.ana)

        self.u_carlos = User.objects.create_user("profesor2", password="clave123")
        self.u_carlos.first_name = "Carlos"
        self.u_carlos.last_name = "Russo"
        self.u_carlos.save()
        Perfil.objects.create(usuario=self.u_carlos, rol=Perfil.DOCENTE, docente=self.carlos)

        self.u_admin = User.objects.create_user("secretaria", password="clave123")
        Perfil.objects.create(usuario=self.u_admin, rol=Perfil.ADMINISTRATIVO)

    def _url(self, materia, cuat=1):
        return reverse("profesor_planilla", kwargs={"cuat": cuat, "materia_id": materia.id})

    def test_el_docente_ve_su_planilla_con_su_nombre(self):
        self.client.force_login(self.u_ana)
        r = self.client.get(self._url(self.materia_ana))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "PROFESOR/A:")
        self.assertContains(r, "Ana Martínez")

    def test_el_docente_no_ve_la_planilla_de_otro(self):
        self.client.force_login(self.u_ana)
        r = self.client.get(self._url(self.materia_carlos), follow=True)
        # lo devuelve a su menú con un aviso
        self.assertRedirects(r, reverse("calificaciones_menu"))
        self.assertContains(r, "No podés consultar esa materia.")

    def test_la_secretaria_ve_las_planillas_de_todos(self):
        self.client.force_login(self.u_admin)
        r = self.client.get(self._url(self.materia_carlos))
        self.assertEqual(r.status_code, 200)
        # con el nombre del docente de esa materia, no el suyo
        self.assertContains(r, "Carlos Russo")
        self.assertNotContains(r, "Ana Martínez")

    def test_la_secretaria_ve_la_planilla_en_modo_lectura(self):
        self.client.force_login(self.u_admin)
        r = self.client.get(self._url(self.materia_ana))
        self.assertNotContains(r, "Guardar cambios")
        self.assertContains(r, "Modo lectura")
        self.assertContains(r, "readonly")

    def test_la_secretaria_no_puede_guardar_en_la_planilla(self):
        self.client.force_login(self.u_admin)
        r = self.client.post(self._url(self.materia_ana), {
            "accion": "guardar", "cursada_1": "R", "dic_1": "7", "feb_1": "",
        }, follow=True)
        self.assertContains(r, "Solo el docente de la materia puede guardar los cambios.")

    def test_el_menu_de_la_secretaria_lista_las_materias(self):
        self.client.force_login(self.u_admin)
        r = self.client.get(reverse("calificaciones_menu"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Planillas de calificaciones")
        self.assertContains(r, "Ana Martínez")
        self.assertContains(r, "Carlos Russo")
        self.assertContains(r, "Laboratorio de Programación")
        self.assertContains(r, "Historia")


# ─────────────────────────────────────────────
#  BOLETÍN (RITE) Y FIRMAS
# ─────────────────────────────────────────────

class RiteTests(TestCase):
    """El boletín del alumno: frente + dorso, listo para imprimir."""

    def setUp(self):
        self.curso = Curso.objects.create(anio=5, division="B")
        self.docente = Docente.objects.create(nombre="Ana", apellido="Prueba", dni="90000031")
        self.materia = Materia.objects.create(
            nombre="Laboratorio de Programación", curso=self.curso, docente=self.docente
        )
        self.cat = CategoriaEvaluacion.objects.create(
            nombre="TP 1", materia=self.materia, orden=1, peso=Decimal("100"),
        )
        self.alumno = Alumno.objects.create(
            nombre="Lucía", apellido="Acosta", dni="90000032",
            fecha_nacimiento=date(2008, 5, 1), anio=self.curso.anio, division=self.curso.division,
        )
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.cat, cuatrimestre=1, valor=Decimal("8"))
        NotaEvaluacion.objects.create(alumno=self.alumno, materia=self.materia,
                                       categoria=self.cat, cuatrimestre=2, valor=Decimal("9"))
        CierreCuatrimestre.objects.create(
            alumno=self.alumno, materia=self.materia, cuatrimestre=1,
            valoracion_preliminar="TEA",
        )
        CierreCuatrimestre.objects.create(
            alumno=self.alumno, materia=self.materia, cuatrimestre=2,
            valoracion_preliminar="TEA", calificacion=Decimal("9"),
        )
        # 1 falta y 4 presentes: 80 % justo, la materia se puede acreditar.
        RegistroAsistencia.objects.create(alumno=self.alumno, materia=self.materia,
                                          fecha=date(2026, 4, 10), estado="A")
        for dia in (11, 12, 13, 14):
            RegistroAsistencia.objects.create(
                alumno=self.alumno, materia=self.materia,
                fecha=date(2026, 4, dia), estado="P",
            )

        self.u_alumno = User.objects.create_user("alumno2", password="clave123")
        Perfil.objects.create(usuario=self.u_alumno, rol=Perfil.ALUMNO, alumno=self.alumno)
        self.u_docente = User.objects.create_user("docente4", password="clave123")
        Perfil.objects.create(usuario=self.u_docente, rol=Perfil.DOCENTE, docente=self.docente)

        # el boletín del año está publicado (fin de año)
        PublicacionBoletin.objects.create(anio=timezone.now().year, publicado=True)

    def test_rite_frente_y_dorso(self):
        self.client.force_login(self.u_alumno)
        r = self.client.get(reverse("alumno_ver_boletin"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "calificaciones/boletin.html")
        for texto in ("REGISTRO INSTITUCIONAL DE TRAYECTORIAS EDUCATIVAS",
                      "Escuela de Educación Secundaria Técnica N° 3",
                      "Región VII",
                      "Acosta, Lucía", "D.N.I.: 90000032",
                      "1° CUATRIMESTRE", "2° CUATRIMESTRE", "PROMEDIO ANUAL",
                      "INTENSIFICACIÓN", "1° cuat.", "Diciembre", "Febrero",
                      "Dorso · Ciclo lectivo",
                      "Materias que intensifican", "PERÍODO DE INTENSIFICACIÓN",
                      "Días hábiles", "Inasistencias",
                      "Firma de", "Director/a", "Adulta/o responsable", "Estudiante",
                      "Laboratorio de Programación"):
            self.assertContains(r, texto)
        # notas del alumno en la fila de la materia
        self.assertContains(r, "TEA")
        self.assertContains(r, "<b>8</b>")
        self.assertContains(r, "<b>9</b>")
        # sin textos de maqueta
        self.assertNotContains(r, "Datos de ejemplo")
        self.assertNotContains(r, "[PRECEPTOR/A]")

    def test_el_boletin_muestra_el_preceptor_de_la_planilla(self):
        PlanillaDatos.objects.create(materia=self.materia, preceptor="Laura Gómez")
        self.client.force_login(self.u_alumno)
        r = self.client.get(reverse("alumno_ver_boletin"))
        self.assertContains(r, "Preceptor/a: Laura Gómez")

    def test_el_boletin_permite_firmar_los_dos_cuatrimestres(self):
        self.client.force_login(self.u_alumno)
        r = self.client.get(reverse("alumno_ver_boletin"))
        self.assertContains(r, 'name="cuat" value="1"')
        self.assertContains(r, 'name="cuat" value="2"')

    def test_el_alumno_firma_solo_por_si_mismo(self):
        self.client.force_login(self.u_alumno)
        r = self.client.post(reverse("confirmar_rite"), {"tipo": "estudiante", "cuat": 1})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ConfirmacionRite.objects.filter(
            alumno=self.alumno, tipo="estudiante", cuatrimestre=1).exists())

        # el alumno no puede registrar la firma del adulto
        self.client.post(reverse("confirmar_rite"), {"tipo": "adulto", "cuat": 1})
        self.assertFalse(ConfirmacionRite.objects.filter(
            alumno=self.alumno, tipo="adulto").exists())

    def test_el_docente_registra_la_firma_del_adulto(self):
        self.client.force_login(self.u_docente)
        r = self.client.post(reverse("confirmar_rite"), {
            "tipo": "adulto", "cuat": 1, "alumno_id": self.alumno.id,
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ConfirmacionRite.objects.filter(
            alumno=self.alumno, tipo="adulto", cuatrimestre=1).exists())

    def test_solo_el_directivo_registra_la_firma_del_director(self):
        self.client.force_login(self.u_docente)
        r = self.client.post(reverse("confirmar_rite"),
                             {"tipo": "director", "cuat": 1, "alumno_id": self.alumno.id}, follow=True)
        self.assertContains(r, "no puede registrar la firma de Director/a")
        self.assertFalse(ConfirmacionRite.objects.filter(tipo="director").exists())

        u_directivo = User.objects.create_user("directivo_rite", password="clave123")
        Perfil.objects.create(usuario=u_directivo, rol=Perfil.DIRECTIVO)
        self.client.force_login(u_directivo)
        self.client.post(reverse("confirmar_rite"), {"tipo": "director", "cuat": 1, "alumno_id": self.alumno.id})
        self.assertTrue(ConfirmacionRite.objects.filter(tipo="director", cuatrimestre=1).exists())

    def test_el_docente_solo_ve_boletines_de_sus_cursos(self):
        otro_curso = Curso.objects.create(anio=3, division="C")
        ajeno = Alumno.objects.create(nombre="Zoe", apellido="Zárate", dni="90000033",
                                      fecha_nacimiento=date(2010, 1, 1), anio=3, division="C")
        self.client.force_login(self.u_docente)
        r = self.client.get(reverse("alumno_seleccionar"))
        self.assertContains(r, "Acosta, Lucía")
        self.assertNotContains(r, "Zárate, Zoe")
        r = self.client.get(reverse("alumno_ver_boletin"), {"alumno_id": ajeno.id}, follow=True)
        self.assertContains(r, "Solo podés ver el boletín de alumnos de tus cursos.")
        self.assertIsNotNone(otro_curso)

    def test_firma_del_segundo_cuatrimestre(self):
        """El boletín permite registrar la firma del 2° cuatrimestre."""
        self.client.force_login(self.u_alumno)
        r = self.client.post(reverse("confirmar_rite"), {"tipo": "estudiante", "cuat": 2})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ConfirmacionRite.objects.filter(
            alumno=self.alumno, tipo="estudiante", cuatrimestre=2).exists())

    def test_boletin_muestra_ted_en_rojo(self):
        CierreCuatrimestre.objects.filter(
            alumno=self.alumno, materia=self.materia, cuatrimestre=1,
        ).update(valoracion_preliminar="TED")
        self.client.force_login(self.u_alumno)
        r = self.client.get(reverse("alumno_ver_boletin"))
        self.assertContains(r, '<span class="ted">TED</span>')

    def test_asistencia_baja_no_muestra_promedio_anual(self):
        """Con 60 % de asistencia el boletín avisa y no da por aprobada la materia."""
        RegistroAsistencia.objects.create(
            alumno=self.alumno, materia=self.materia,
            fecha=date(2026, 4, 15), estado="A",
        )
        self.client.force_login(self.u_alumno)
        r = self.client.get(reverse("alumno_ver_boletin"))
        self.assertContains(r, 'title="Asistencia menor al 80 %')
        # el promedio 8,5 no se muestra porque la materia no se acredita
        self.assertNotContains(r, "<b>8.5</b>")

    def test_el_boletin_muestra_cursada_y_mesas_de_cualquier_cuatrimestre(self):
        """La planilla guarda C/R, diciembre y febrero en el cuatrimestre que se
        mira: el boletín los muestra igual, estén en el 1° o en el 2°."""
        CierreCuatrimestre.objects.filter(cuatrimestre=1).update(nota_diciembre=Decimal("7"))
        CierreCuatrimestre.objects.filter(cuatrimestre=2).update(cursada="R", nota_febrero=Decimal("8"))
        self.client.force_login(self.u_alumno)
        fila = self.client.get(reverse("alumno_ver_boletin")).context["filas"][0]
        self.assertEqual(fila["cursada"], "R")
        self.assertEqual(fila["dic"], "7")
        self.assertEqual(fila["feb"], "8")


# ─────────────────────────────────────────────
#  PUBLICACIÓN ANUAL DEL BOLETÍN
# ─────────────────────────────────────────────

class PublicacionBoletinTests(TestCase):
    """Regla: el alumno nunca ve el boletín hasta que secretaría lo publica."""

    def setUp(self):
        self.curso = Curso.objects.create(anio=5, division="B")
        self.docente = Docente.objects.create(nombre="Ana", apellido="Prueba", dni="90000051")
        self.materia = Materia.objects.create(
            nombre="Historia", curso=self.curso, docente=self.docente
        )
        self.alumno = Alumno.objects.create(
            nombre="Lucía", apellido="Acosta", dni="90000052",
            fecha_nacimiento=date(2008, 5, 1), anio=self.curso.anio, division=self.curso.division,
        )

        self.u_alumno = User.objects.create_user("alumno_pub", password="clave123")
        Perfil.objects.create(usuario=self.u_alumno, rol=Perfil.ALUMNO, alumno=self.alumno)
        self.u_docente = User.objects.create_user("docente_pub", password="clave123")
        Perfil.objects.create(usuario=self.u_docente, rol=Perfil.DOCENTE, docente=self.docente)
        self.u_admin = User.objects.create_user("admin_pub", password="clave123")
        Perfil.objects.create(usuario=self.u_admin, rol=Perfil.ADMINISTRATIVO)
        self.u_directivo = User.objects.create_user("directivo_pub", password="clave123")
        Perfil.objects.create(usuario=self.u_directivo, rol=Perfil.DIRECTIVO)

    def _publicar(self, publicado=True):
        PublicacionBoletin.objects.update_or_create(
            anio=timezone.now().year, defaults={"publicado": publicado},
        )

    def test_alumno_no_ve_el_boletin_antes_de_publicar(self):
        self.client.force_login(self.u_alumno)
        r = self.client.get(reverse("alumno_ver_boletin"), follow=True)
        self.assertRedirects(r, reverse("calificaciones_menu"))
        self.assertContains(r, "El boletín se habilita a fin de año")

    def test_alumno_ve_el_boletin_despues_de_publicar(self):
        self._publicar()
        self.client.force_login(self.u_alumno)
        r = self.client.get(reverse("alumno_ver_boletin"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "REGISTRO INSTITUCIONAL DE TRAYECTORIAS EDUCATIVAS")

    def test_docente_no_ve_el_boletin_antes_de_publicar(self):
        self.client.force_login(self.u_docente)
        r = self.client.get(
            reverse("alumno_ver_boletin"), {"alumno_id": self.alumno.id}, follow=True,
        )
        self.assertRedirects(r, reverse("calificaciones_menu"))

    def test_secretaria_y_directivo_siempre_ven_el_boletin(self):
        for user in (self.u_admin, self.u_directivo):
            with self.subTest(usuario=user.username):
                self.client.force_login(user)
                r = self.client.get(
                    reverse("alumno_ver_boletin"), {"alumno_id": self.alumno.id},
                )
                self.assertEqual(r.status_code, 200)

    def test_confirmar_rite_bloqueado_antes_de_publicar(self):
        self.client.force_login(self.u_alumno)
        r = self.client.post(
            reverse("confirmar_rite"), {"tipo": "estudiante", "cuat": 1}, follow=True,
        )
        self.assertRedirects(r, reverse("calificaciones_menu"))
        self.assertFalse(ConfirmacionRite.objects.filter(alumno=self.alumno).exists())

    def test_solo_secretaria_y_directivo_publican(self):
        for user in (self.u_alumno, self.u_docente):
            with self.subTest(usuario=user.username):
                self.client.force_login(user)
                r = self.client.post(reverse("publicar_boletines"))
                self.assertEqual(r.status_code, 302)
                self.assertEqual(r.url, "/")
        self.assertFalse(PublicacionBoletin.objects.filter(publicado=True).exists())

    def test_el_interruptor_publica_y_oculta(self):
        self.client.force_login(self.u_admin)
        url = reverse("publicar_boletines")

        self.client.post(url)
        pub = PublicacionBoletin.objects.get(anio=timezone.now().year)
        self.assertTrue(pub.publicado)
        self.assertIsNotNone(pub.fecha_publicacion)
        self.assertEqual(pub.usuario, "admin_pub")

        self.client.post(url)
        pub.refresh_from_db()
        self.assertFalse(pub.publicado)
        self.assertIsNone(pub.fecha_publicacion)

    def test_el_menu_de_secretaria_muestra_el_interruptor(self):
        """Secretaría/directivo ven el botón para publicar u ocultar el año."""
        self.client.force_login(self.u_admin)
        r = self.client.get(reverse("calificaciones_menu"))
        self.assertContains(r, "Publicar boletines del año")

        self.client.post(reverse("publicar_boletines"))
        r = self.client.get(reverse("calificaciones_menu"))
        self.assertContains(r, "Ocultar boletines del año")

    def test_el_menu_del_alumno_avisa_y_luego_muestra_el_boton(self):
        self.client.force_login(self.u_alumno)
        r = self.client.get(reverse("calificaciones_menu"))
        self.assertContains(r, "El boletín se habilita a fin de año")
        self.assertNotContains(r, "Ver boletín completo")

        self._publicar()
        r = self.client.get(reverse("calificaciones_menu"))
        self.assertContains(r, "Ver boletín completo")


# ─────────────────────────────────────────────
#  MATERIAS CON EL MISMO NOMBRE EN DOS CURSOS
# ─────────────────────────────────────────────

class MateriaRepetidaTests(TestCase):
    """Las URLs usan el id: 'Inglés' de 5° A y de 5° B no se mezclan."""

    def setUp(self):
        self.curso_a = Curso.objects.create(anio=5, division="A")
        self.curso_b = Curso.objects.create(anio=5, division="B")
        self.docente = Docente.objects.create(nombre="Eva", apellido="Paz", dni="90000061")
        self.ingles_a = Materia.objects.create(nombre="Inglés", curso=self.curso_a, docente=self.docente)
        self.ingles_b = Materia.objects.create(nombre="Inglés", curso=self.curso_b, docente=self.docente)
        CategoriaEvaluacion.objects.create(nombre="Oral A", materia=self.ingles_a, orden=1)
        CategoriaEvaluacion.objects.create(nombre="Escrito B", materia=self.ingles_b, orden=1)
        Alumno.objects.create(nombre="Ana", apellido="Alonso", dni="90000062",
                              fecha_nacimiento=date(2008, 1, 1), anio=5, division="A")
        Alumno.objects.create(nombre="Beto", apellido="Blanco", dni="90000063",
                              fecha_nacimiento=date(2008, 1, 1), anio=5, division="B")
        self.u_docente = User.objects.create_user("docente_rep", password="clave123")
        Perfil.objects.create(usuario=self.u_docente, rol=Perfil.DOCENTE, docente=self.docente)
        self.client.force_login(self.u_docente)

    def test_el_menu_muestra_las_dos_materias(self):
        r = self.client.get(reverse("calificaciones_menu"))
        self.assertEqual(r.context["total_materias"], 2)
        self.assertContains(r, "5° A")
        self.assertContains(r, "5° B")

    def test_cada_materia_muestra_solo_su_curso(self):
        url = reverse("profesor_cargar_notas", kwargs={"cuat": 1, "materia_id": self.ingles_a.id})
        r = self.client.get(url)
        self.assertContains(r, "Alonso, Ana")
        self.assertContains(r, "Oral A")
        self.assertNotContains(r, "Blanco, Beto")
        self.assertNotContains(r, "Escrito B")
