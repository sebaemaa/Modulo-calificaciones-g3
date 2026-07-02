from django.db import models
# Importa el módulo 'models' de Django, que contiene las clases base del ORM
# (Model, ForeignKey, CharField, DecimalField, etc.) necesarias para mapear
# clases de Python a tablas de la base de datos.


class Calificacion(models.Model):
    # Hereda de models.Model → Django la registra como modelo del ORM.
    # Cada instancia = una fila. Cada atributo = una columna.
    # Django genera la tabla como "calificaciones_calificacion".

    PERIODOS = [
        ('1C', '1° Cuatrimestre'),
        ('2C', '2° Cuatrimestre'),
        ('3C', '3° Cuatrimestre'),
        ('4C', '4° Cuatrimestre'),
    ]
    # Constante de clase con las opciones válidas para el campo 'periodo'.
    # Cada tupla es (valor_guardado_en_bd, texto_visible_para_el_usuario).

    alumno = models.ForeignKey(
        'alumnos.Alumno',          # Referencia en string al modelo Alumno de la
                                    # app 'alumnos', para evitar import circular.
        on_delete=models.CASCADE,  # Si se borra un Alumno, se borran en cascada
                                    # todas sus Calificaciones asociadas.
        related_name='calificaciones'
        # Permite acceder con alumno.calificaciones.all()
        # en vez del default alumno.calificacion_set.all().
    )
    # Relación muchos-a-uno: muchas Calificaciones → un Alumno.
    # A nivel BD crea una columna 'alumno_id' (entero, FK).

    materia = models.ForeignKey(
        'docentes.Materia',        # Referencia en string al modelo Materia,
                                    # que vive en la app 'docentes'.
        on_delete=models.CASCADE,  # Si se borra la Materia, se borran sus Calificaciones.
        related_name='calificaciones'
        # Permite acceder con materia.calificaciones.all().
    )
    # Relación muchos-a-uno: muchas Calificaciones → una Materia.
    # Crea la columna 'materia_id' (entero, FK).

    periodo = models.CharField(max_length=2, choices=PERIODOS)
    # Texto de hasta 2 caracteres (ej: '1C'). choices=PERIODOS liga el campo
    # a la lista de opciones definida arriba: genera un <select> automático
    # en formularios/admin y valida el valor al hacer full_clean().

    nota = models.DecimalField(max_digits=4, decimal_places=2)
    # DecimalField en vez de FloatField: evita errores de redondeo de punto
    # flotante, importante para un valor exacto como una nota.
    # max_digits=4 → total de dígitos permitidos (ej: 10.00).
    # decimal_places=2 → cuántos van después de la coma.

    def __str__(self):
        return f"{self.alumno} - {self.materia} - {self.periodo}: {self.nota}"
    # Define cómo se representa el objeto como texto (admin, shell, etc.).

    class Meta:
        # Configuración del modelo: no crea columnas, define metadatos.

        verbose_name = "Calificación"
        # Nombre legible en singular, usado en el admin.

        verbose_name_plural = "Calificaciones"
        # Nombre legible en plural, usado en el admin.

        unique_together = [('alumno', 'materia', 'periodo')]
        # Constraint de unicidad compuesta: no puede haber dos registros
        # con la misma combinación exacta de (alumno, materia, periodo).
        # Evita cargar dos notas para el mismo alumno, en la misma materia
        # y el mismo período.

        ordering = ['alumno', 'materia', 'periodo']
        # Orden por defecto al hacer Calificacion.objects.all(),
        # sin necesidad de usar .order_by() manualmente.


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