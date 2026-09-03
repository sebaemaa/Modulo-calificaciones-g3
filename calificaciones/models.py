from django.db import models


class AlumnoCalificacion(models.Model):
    """Alumno cargado por el profesor en una materia concreta.

    NOTA DE INTEGRACIÓN: este módulo es autocontenido (porque cada grupo
    trabaja aislado). Para unir después con el padrón real (alumnos.Alumno),
    se usa el DNI como clave natural. Los nombres de materia deben cargarse
    con nombres canónicos para matchear con docentes.Materia.
    """
    apellido = models.CharField(max_length=100, blank=True, default="")
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, blank=True, default="",
                           verbose_name="DNI", help_text="Clave para unir con el padrón real")
    curso = models.CharField(max_length=5)
    division = models.CharField(max_length=2)
    materia = models.CharField(max_length=50)

    def __str__(self):
        if self.apellido:
            return f"{self.apellido}, {self.nombre} — {self.materia}"
        return f"{self.nombre} — {self.materia}"

    class Meta:
        verbose_name = "Calificación de alumno"
        verbose_name_plural = "Calificaciones de alumnos"
        ordering = ['apellido', 'nombre']
        unique_together = [('nombre', 'apellido', 'materia')]


class CategoriaEvaluacion(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: Trabajo Práctico, Examen, Participación")
    materia_nombre = models.CharField(max_length=50, help_text="Nombre exacto de la materia")
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la grilla")

    def __str__(self):
        return f"{self.nombre} — {self.materia_nombre}"

    class Meta:
        verbose_name = "Categoría de evaluación"
        verbose_name_plural = "Categorías de evaluación"
        ordering = ['materia_nombre', 'orden', 'nombre']


class NotaEvaluacion(models.Model):
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]

    alumno_calificacion = models.ForeignKey(
        AlumnoCalificacion,
        on_delete=models.CASCADE,
        related_name='notas'
    )
    categoria = models.ForeignKey(
        CategoriaEvaluacion,
        on_delete=models.CASCADE,
        related_name='notas'
    )
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES)
    valor = models.DecimalField(max_digits=4, decimal_places=1)
    descripcion = models.CharField(max_length=200, blank=True, help_text="Ej: Primer parcial, TP N°3")
    fecha = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.alumno_calificacion.nombre} - {self.categoria.nombre}: {self.valor}"

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
