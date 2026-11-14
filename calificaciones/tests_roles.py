"""Tests de roles y permisos del módulo calificaciones.

Verifican que cada rol vea solo lo que le corresponde: el docente en sus
materias, el alumno solo en su propia ficha, y el administrativo sin acceso a
las funciones de carga de notas.

    python manage.py test calificaciones.tests_roles
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from alumnos.models import Alumno, Curso
from cuentas.models import Perfil
from docentes.models import Docente, Materia

from .models import BoletinConfig, CategoriaEvaluacion, NotaEvaluacion, PublicacionBoletin
from . import urls as calificaciones_urls


class RolesCalificacionesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.curso = Curso.objects.create(anio=1, division="A")

        cls.alumno_a = Alumno.objects.create(
            nombre="Ana",
            apellido="Alvarez",
            dni="10000001",
            fecha_nacimiento=date(2010, 1, 1),
            anio=cls.curso.anio,
            division=cls.curso.division,
            activo=True,
        )
        cls.alumno_b = Alumno.objects.create(
            nombre="Beto",
            apellido="Benitez",
            dni="10000002",
            fecha_nacimiento=date(2010, 2, 2),
            anio=cls.curso.anio,
            division=cls.curso.division,
            activo=True,
        )

        cls.docente = Docente.objects.create(
            nombre="Dora",
            apellido="Docente",
            dni="20000001",
            activo=True,
        )
        cls.materia = Materia.objects.create(
            nombre="Matematica",
            curso=cls.curso,
            docente=cls.docente,
        )
        cls.categoria = CategoriaEvaluacion.objects.create(
            nombre="Trabajo Practico",
            materia=cls.materia,
            orden=1,
        )

        cls.user_alumno_a = cls._crear_usuario("alumno_a", "alumno", alumno=cls.alumno_a)
        cls.user_alumno_b = cls._crear_usuario("alumno_b", "alumno", alumno=cls.alumno_b)
        cls.user_docente = cls._crear_usuario("docente_user", "docente", docente=cls.docente)
        cls.user_admin = cls._crear_usuario("admin_user", "administrativo")

        BoletinConfig.objects.create(cuatrimestre=1, publicado=True)
        PublicacionBoletin.objects.create(anio=timezone.now().year, publicado=True)

    @classmethod
    def _crear_usuario(cls, username, rol, alumno=None, docente=None):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            username=username,
            password="clave-de-prueba-123",
        )
        Perfil.objects.create(
            usuario=user,
            rol=rol,
            alumno=alumno,
            docente=docente,
        )
        return user

    def _kwargs_para(self, pattern):
        kwargs = {}
        for key in pattern.pattern.converters:
            if key == "cuat":
                kwargs[key] = 1
            elif key == "materia_id":
                kwargs[key] = self.materia.id
            elif key == "cat_id":
                kwargs[key] = self.categoria.id
            else:
                raise AssertionError(f"Converter sin datos de prueba: {key}")
        return kwargs

    def _urls_del_modulo(self):
        for pattern in calificaciones_urls.urlpatterns:
            if not pattern.name:
                continue
            yield pattern.name, reverse(pattern.name, kwargs=self._kwargs_para(pattern))

    def _login(self, user):
        self.client.force_login(user)

    def test_a_anonimo_redirige_a_login_en_todas_las_vistas(self):
        urls = list(self._urls_del_modulo())
        self.assertTrue(urls, "No se encontraron urls del modulo")

        for nombre, url in urls:
            with self.subTest(url=nombre):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    302,
                    f"{nombre} no redirigio (status {response.status_code})",
                )
                self.assertTrue(
                    response.url.startswith("/accounts/login/"),
                    f"{nombre} redirigio a {response.url} en vez del login",
                )

    def test_b_alumno_no_accede_a_vistas_de_profesor(self):
        self._login(self.user_alumno_a)

        nombres = [
            name
            for name, _ in self._urls_del_modulo()
            if name.startswith("profesor_")
        ]
        self.assertTrue(nombres, "No se encontraron vistas profesor_*")

        for pattern in calificaciones_urls.urlpatterns:
            if not pattern.name or not pattern.name.startswith("profesor_"):
                continue
            url = reverse(pattern.name, kwargs=self._kwargs_para(pattern))
            with self.subTest(url=pattern.name):
                response = self.client.get(url)
                self.assertNotEqual(response.status_code, 200)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, "/")

        url_guardar = reverse(
            "profesor_guardar_nota",
            kwargs={"cuat": 1, "materia_id": self.materia.id},
        )
        response = self.client.post(
            url_guardar,
            {"alumno_id": self.alumno_a.id, "cat_id": self.categoria.id, "valor": "9"},
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

        response = self.client.get(reverse("alumno_seleccionar"))
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_c_alumno_a_ignora_alumno_id_de_b(self):
        self._login(self.user_alumno_a)

        url_boletin = reverse("alumno_ver_boletin")
        response = self.client.get(url_boletin, {"alumno_id": self.alumno_b.id})
        self.assertEqual(response.status_code, 200)
        contenido = response.content.decode()
        self.assertIn("Alvarez, Ana", contenido)
        self.assertNotIn("Benitez, Beto", contenido)

    def test_d_administrativo(self):
        self._login(self.user_admin)

        url_cargar = reverse(
            "profesor_cargar_notas",
            kwargs={"cuat": 1, "materia_id": self.materia.id},
        )
        response = self.client.get(url_cargar)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

        response = self.client.get(reverse("alumno_seleccionar"))
        self.assertEqual(response.status_code, 200)

    def test_e_docente(self):
        self._login(self.user_docente)

        self.assertEqual(self.client.get(reverse("calificaciones_menu")).status_code, 200)
        self.assertEqual(self.client.get(reverse("alumno_seleccionar")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("profesor_planilla",
                                     kwargs={"cuat": 1, "materia_id": self.materia.id})).status_code,
            200,
        )

    def test_f_menu_segun_rol(self):
        url_menu = reverse("calificaciones_menu")

        self._login(self.user_alumno_a)
        contenido = self.client.get(url_menu).content.decode()
        self.assertIn("Mi boletín", contenido)
        self.assertNotIn("Profesor", contenido)

        self._login(self.user_docente)
        contenido = self.client.get(url_menu).content.decode()
        self.assertIn("Mis materias", contenido)
        self.assertIn("Cargar notas", contenido)

        self._login(self.user_admin)
        contenido = self.client.get(url_menu).content.decode()
        self.assertNotIn("Profesor", contenido)

    def test_g_docente_guarda_nota(self):
        self._login(self.user_docente)

        url = reverse(
            "profesor_guardar_nota",
            kwargs={"cuat": 1, "materia_id": self.materia.id},
        )
        response = self.client.post(
            url,
            {"alumno_id": self.alumno_a.id, "cat_id": self.categoria.id, "valor": "8"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("ok"))

        nota = NotaEvaluacion.objects.filter(
            alumno=self.alumno_a,
            materia=self.materia,
            categoria=self.categoria,
            cuatrimestre=1,
        ).first()
        self.assertIsNotNone(nota)
        self.assertEqual(nota.valor, Decimal("8"))
