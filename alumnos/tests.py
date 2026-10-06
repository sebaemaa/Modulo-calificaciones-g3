from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest, QueryDict
from django.test import TestCase
from django.utils.datastructures import MultiValueDict

from .models import Alumno
from .views import index


class AlumnoDocumentacionTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin",
            password="admin1234",
            is_staff=True,
            is_superuser=True,
        )

    def _post_alumno(self, dni, archivos=None):
        data = {
            "nombre": "Lucía",
            "apellido": "Gómez",
            "dni": dni,
            "fecha_nacimiento": "2012-05-10",
            "domicilio": "Av. Siempre Viva 123",
            "telefono_contacto": "1144556677",
            "anio": "1",
            "division": "A",
        }
        request = HttpRequest()
        request.method = "POST"
        request.user = self.admin_user
        request.POST = QueryDict("", mutable=True)
        for key, value in data.items():
            request.POST[key] = str(value)
        if archivos:
            request.FILES = MultiValueDict({"documentacion": archivos})
        return index(request)

    def test_crear_alumno_con_documentacion(self):
        archivo = SimpleUploadedFile(
            "constancia.pdf",
            b"%PDF-1.4\n%test",
            content_type="application/pdf",
        )

        response = self._post_alumno("40111222", [archivo])

        self.assertEqual(response.status_code, 302)
        alumno = Alumno.objects.get(dni="40111222")
        self.assertTrue(alumno.documentacion)
        self.assertIn("constancia", alumno.documentacion.name)

    def test_subir_varios_archivos_en_carpeta_del_alumno(self):
        primer_archivo = SimpleUploadedFile(
            "foto1.jpg",
            b"fake-image-1",
            content_type="image/jpeg",
        )
        segundo_archivo = SimpleUploadedFile(
            "constancia.pdf",
            b"%PDF-1.4\n%test",
            content_type="application/pdf",
        )

        response = self._post_alumno("40223333", [primer_archivo, segundo_archivo])

        self.assertEqual(response.status_code, 302)
        alumno = Alumno.objects.get(dni="40223333")
        self.assertGreaterEqual(len(alumno.documentacion_archivos), 2)
        self.assertIn("foto1.jpg", alumno.documentacion_archivos)
        self.assertIn("constancia.pdf", alumno.documentacion_archivos)

    def test_detalle_de_archivos_incluye_fecha_y_hora(self):
        archivo = SimpleUploadedFile(
            "constancia_detalle.pdf",
            b"%PDF-1.4\n%test",
            content_type="application/pdf",
        )

        response = self._post_alumno("40334444", [archivo])

        self.assertEqual(response.status_code, 302)
        alumno = Alumno.objects.get(dni="40334444")
        detalle = alumno.documentacion_archivos_detalle

        self.assertTrue(detalle)
        self.assertTrue(detalle[0]["nombre"].endswith(".pdf"))
        self.assertIn("fecha_label", detalle[0])
        self.assertIn("hora", detalle[0])
