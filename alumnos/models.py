from django.db import models

# ================================================================
# MÓDULO 1 — GESTIÓN DE ALUMNOS
# Grupo responsable: [nombre del grupo]
# ATENCIÓN: Esta tabla es la principal del sistema.
# Los demás módulos la consultan pero NO la modifican.
# ================================================================

class Curso(models.Model):
    anio = models.IntegerField(verbose_name="Año")
    division = models.CharField(max_length=10, verbose_name="División")

    def __str__(self):
        return f"{self.anio}° {self.division}"

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['anio', 'division']


class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    domicilio = models.CharField(max_length=200, blank=True)
    telefono_contacto = models.CharField(max_length=50, blank=True, verbose_name="Teléfono de contacto")
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name='alumnos')
    activo = models.BooleanField(default=True)  # baja lógica

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (DNI: {self.dni})"

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ['apellido', 'nombre']
