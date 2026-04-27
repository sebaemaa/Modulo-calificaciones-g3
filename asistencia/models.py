from django.db import models

# ================================================================
# MÓDULO 2 — GESTIÓN DE ASISTENCIA
# Grupo responsable: [nombre del grupo]
# Consulta tablas de: alumnos, docentes
# ================================================================

ESTADO_CHOICES = [
    ('P', 'Presente'),
    ('A', 'Ausente'),
    ('T', 'Tardanza'),
]

class RegistroAsistencia(models.Model):
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='asistencias')
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES)

    def __str__(self):
        return f"{self.alumno} — {self.materia} — {self.fecha} — {self.get_estado_display()}"

    class Meta:
        verbose_name = "Registro de asistencia"
        verbose_name_plural = "Registros de asistencia"
        unique_together = ('alumno', 'materia', 'fecha')
        ordering = ['-fecha']
