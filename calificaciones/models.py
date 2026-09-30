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


class CategoriaEvaluacion(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: Trabajo Práctico, Examen, Participación")
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='categorias')
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la grilla")

    def __str__(self):
        return f"{self.nombre} — {self.materia}"

    class Meta:
        verbose_name = "Categoría de evaluación"
        verbose_name_plural = "Categorías de evaluación"
        ordering = ['materia', 'orden', 'nombre']


class NotaEvaluacion(models.Model):
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]

    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='notas_evaluacion')
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='notas_evaluacion')
    categoria = models.ForeignKey(CategoriaEvaluacion, on_delete=models.CASCADE, related_name='notas')
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES)
    valor = models.DecimalField(max_digits=4, decimal_places=1)
    descripcion = models.CharField(max_length=200, blank=True, help_text="Ej: Primer parcial, TP N°3")
    fecha = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.alumno} - {self.categoria.nombre}: {self.valor}"

    class Meta:
        verbose_name = "Nota de evaluación"
        verbose_name_plural = "Notas de evaluación"


class BoletinConfig(models.Model):
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]

    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES, unique=True)
    publicado = models.BooleanField(default=False)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        estado = "Publicado" if self.publicado else "Oculto"
        return f"Boletín {self.get_cuatrimestre_display()} — {estado}"

    class Meta:
        verbose_name = "Configuración de boletín"
        verbose_name_plural = "Configuraciones de boletines"