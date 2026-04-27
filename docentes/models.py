from django.db import models

# ================================================================
# MÓDULO 4 — GESTIÓN DE DOCENTES Y MATERIAS
# Grupo responsable: [nombre del grupo]
# ATENCIÓN: Esta tabla es consultada por otros módulos.
# Los demás grupos NO la modifican.
# ================================================================

class Docente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI")
    contacto = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ['apellido', 'nombre']


class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    curso = models.ForeignKey('alumnos.Curso', on_delete=models.PROTECT, related_name='materias')
    docente = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True, blank=True, related_name='materias')

    def __str__(self):
        return f"{self.nombre} — {self.curso}"

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"


DIAS = [
    ('LUN', 'Lunes'), ('MAR', 'Martes'), ('MIE', 'Miércoles'),
    ('JUE', 'Jueves'), ('VIE', 'Viernes'),
]

class HorarioBloque(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='horarios')
    dia = models.CharField(max_length=3, choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.materia} — {self.get_dia_display()} {self.hora_inicio}"

    class Meta:
        verbose_name = "Bloque horario"
        verbose_name_plural = "Bloques horarios"
