from django.db import models

class Calificacion(models.Model):
    PERIODOS = [
        ('1B', '1° Bimestre'),
        ('2B', '2° Bimestre'),
        ('3B', '3° Bimestre'),
        ('4B', '4° Bimestre'),
    ]

    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='calificaciones')
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='calificaciones')
    periodo = models.CharField(max_length=2, choices=PERIODOS)
    nota = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"{self.alumno} - {self.materia} - {self.periodo}: {self.nota}"

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        unique_together = [('alumno', 'materia', 'periodo')]
        ordering = ['alumno', 'materia', 'periodo']


class AlumnoCalificacion(models.Model):
    nombre = models.CharField(max_length=100)
    curso = models.CharField(max_length=5)
    division = models.CharField(max_length=2)
    materia = models.CharField(max_length=50)
    nota1 = models.IntegerField()
    nota2 = models.IntegerField()

    def __str__(self):
        return f"{self.nombre} — {self.materia}"

    class Meta:
        verbose_name = "Calificación de alumno"
        verbose_name_plural = "Calificaciones de alumnos"
