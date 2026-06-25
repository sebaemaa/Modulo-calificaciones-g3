from django.db import models # Importa las herramientas necesarias para definir la estructura de datos (ORM)

class Calificacion(models.Model): # Crea la clase que representa la tabla 'Calificacion' en la base de datos
    PERIODOS = [ # Define una lista de tuplas para las opciones del campo 'periodo' (opción interna, etiqueta legible)
        ('1B', '1° Bimestre'),
        ('2B', '2° Bimestre'),
        ('3B', '3° Bimestre'),
        ('4B', '4° Bimestre'),
    ]

    alumno = models.ForeignKey( # Define una relación de muchos a uno: muchas calificaciones pueden pertenecer a un alumno
        'alumnos.Alumno', # Indica el modelo relacionado (App alumnos, modelo Alumno)
        on_delete=models.CASCADE, # Si el alumno es eliminado, sus calificaciones también se borrarán automáticamente
        related_name='calificaciones', # Permite acceder a las notas desde el objeto alumno (ej: mi_alumno.calificaciones.all())
    )
    materia = models.ForeignKey( # Define una relación de muchos a uno: muchas calificaciones para una materia
        'docentes.Materia', # Indica el modelo relacionado (App docentes, modelo Materia)
        on_delete=models.CASCADE, # Si la materia es eliminada, las calificaciones asociadas se borrarán
        related_name='calificaciones', # Permite acceder a las notas desde el objeto materia
    )
    periodo = models.CharField(max_length=2, choices=PERIODOS) # Campo de texto limitado a 2 caracteres que usa la lista anterior como selector
    nota = models.DecimalField(max_digits=4, decimal_places=2) # Campo numérico: permite hasta 99.99 (4 dígitos totales, 2 decimales)

    class Meta: # Configuración adicional de metadatos para este modelo
        verbose_name = 'Calificación' # Nombre legible en singular para el panel de administración
        verbose_name_plural = 'Calificaciones' # Nombre legible en plural para el panel de administración
        ordering = ['alumno', 'materia', 'periodo'] # Define el orden en que se listarán las notas por defecto
        unique_together = [('alumno', 'materia', 'periodo')] # Restricción única: no puede haber dos notas del mismo alumno en la misma materia y bimestre

    def __str__(self): # Método especial para definir cómo se mostrará el objeto como texto
        return f"{self.alumno} - {self.materia} - {self.periodo}: {self.nota}" # Formato de visualización: ej "Juan Perez - Matemáticas - 1B: 9.50"