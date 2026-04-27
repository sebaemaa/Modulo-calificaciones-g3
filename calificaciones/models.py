from django.db import models

# ================================================================
# MÓDULO 3 — GESTIÓN DE CALIFICACIONES
# Grupo responsable: [nombre del grupo]
# Consulta tablas de: alumnos, docentes
# ================================================================

PERIODO_CHOICES = [
    ('1B', '1° Bimestre'),
    ('2B', '2° Bimestre'),
    ('3B', '3° Bimestre'),
    ('4B', '4° Bimestre'),
]

class Calificacion(models.Model):
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='calificaciones')
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='calificaciones')
    periodo = models.CharField(max_length=2, choices=PERIODO_CHOICES)
    nota = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"{self.alumno} — {self.materia} — {self.get_periodo_display()}: {self.nota}"

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        unique_together = ('alumno', 'materia', 'periodo')
        ordering = ['alumno', 'materia', 'periodo']
