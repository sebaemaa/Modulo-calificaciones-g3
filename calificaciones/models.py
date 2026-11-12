"""Modelos del Módulo 3 — Gestión de Calificaciones.

Se guardan las notas por categoría de evaluación, el cierre de cada
cuatrimestre (valoración RITE, notas de diciembre/febrero y final) y la
publicación anual del boletín. Las inasistencias no se guardan acá: se leen
del módulo Asistencia.

El módulo consulta las tablas de alumnos y docentes, pero no las modifica:
los datos propios de la planilla viven acá.
"""
from django.db import models

# ================================================================
# MÓDULO 3 — GESTIÓN DE CALIFICACIONES
# Grupo responsable: Grupo 3
# Consulta tablas de: alumnos, docentes
# ================================================================

# ─────────────────────────────────────────────
#  CALIFICACIONES POR PERÍODO (registro simple)
# ─────────────────────────────────────────────

PERIODO_CHOICES = [
    ('1B', '1° Bimestre'),
    ('2B', '2° Bimestre'),
    ('3B', '3° Bimestre'),
    ('4B', '4° Bimestre'),
]


class Calificacion(models.Model):
    """Calificación por bimestre del esqueleto original.

    No la usa ninguna pantalla del módulo: queda para no romper el esqueleto
    que armó el profesor (su tabla ya existe en la base).
    """
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
    """Columna de la grilla de notas (TP, examen, participación...).

    El campo ``grupo`` permite que varias columnas sumen un mismo peso y el
    campo ``peso`` define cuánto aporta a la calificación del cuatrimestre.
    """
    nombre = models.CharField(max_length=100, help_text="Ej: Trabajo Práctico, Examen, Participación")
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='categorias')
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la grilla")
    grupo = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Agrupa columnas en la planilla (ej: Trabajos prácticos)",
    )
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="% que aporta la categoría a la calificación (ej: 30)",
    )

    def __str__(self):
        return f"{self.nombre} — {self.materia}"

    class Meta:
        verbose_name = "Categoría de evaluación"
        verbose_name_plural = "Categorías de evaluación"
        ordering = ['materia', 'orden', 'nombre']


class NotaEvaluacion(models.Model):
    """Nota de un alumno en una categoría y cuatrimestre."""
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
    """Configuración vieja por cuatrimestre (una sola para toda la escuela).

    Ya no la usa ninguna pantalla: la fecha de cierre ahora se guarda por
    materia en ``CierreCuatrimestre.fecha_cierre`` y la publicación del
    boletín es anual (``PublicacionBoletin``). Queda para no perder datos.
    """
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


# ─────────────────────────────────────────────
#  CIERRE DEL CUATRIMESTRE
# ─────────────────────────────────────────────

class CierreCuatrimestre(models.Model):
    """Cierre de un alumno en una materia para un cuatrimestre (RITE).

    Guarda la valoración de trayectoria que elige el docente al cargar
    notas, la cursada (C/R), las notas de diciembre / febrero y, al cerrar
    el cuatrimestre, la calificación oficial y la fecha de cierre.

    ``calificacion_final`` significa algo distinto según el cuatrimestre:
    - 1° cuatrimestre: con ``intensificacion`` marcada, es la nota con la que
      el alumno aprobó al intensificar (columna "Intensificación 1° cuat.").
    - 2° cuatrimestre: es la nota final del año cargada a mano. Si está
      vacía, la planilla la calcula sola con el promedio de los dos.
    """
    TEA = 'TEA'
    TEP = 'TEP'
    TED = 'TED'
    VALORACION_CHOICES = [
        (TEA, 'Trayectoria Educativa Avanzada'),
        (TEP, 'Trayectoria Educativa en Proceso'),
        (TED, 'Trayectoria Educativa Discontinua'),
    ]
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]
    CURSADA_CHOICES = [
        ('C', 'Cursa por primera vez'),
        ('R', 'Recursa'),
    ]

    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='cierres_cuatrimestre')
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='cierres_cuatrimestre')
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES)
    cursada = models.CharField(
        max_length=1, choices=CURSADA_CHOICES, default='C',
        help_text='C: cursa por primera vez · R: recursa',
    )
    valoracion_preliminar = models.CharField(max_length=3, choices=VALORACION_CHOICES, blank=True, default='')
    calificacion = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    intensificacion = models.BooleanField(default=False, help_text='Necesita intensificación en el cuatrimestre')
    nota_diciembre = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    nota_febrero = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    calificacion_final = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cerrado = models.BooleanField(default=False)
    fecha_cierre = models.DateTimeField(null=True, blank=True, help_text='Cuándo el docente cerró el cuatrimestre')

    def __str__(self):
        valoracion = self.valoracion_preliminar or 'sin valorar'
        return f"{self.alumno} — {self.materia} — {self.cuatrimestre}° cuat.: {valoracion}"

    class Meta:
        verbose_name = "Cierre de cuatrimestre"
        verbose_name_plural = "Cierres de cuatrimestre"
        unique_together = ('alumno', 'materia', 'cuatrimestre')
        ordering = ['materia', 'alumno']


# ─────────────────────────────────────────────
#  BOLETÍN (RITE) Y PUBLICACIÓN ANUAL
# ─────────────────────────────────────────────

class ConfirmacionRite(models.Model):
    """Quién tomó conocimiento del RITE (boletín) y cuándo.

    El sistema guarda quién y cuándo, como dice la leyenda del RITE.
    """
    TIPO_CHOICES = [
        ('director', 'Director/a'),
        ('adulto', 'Adulta/o responsable'),
        ('estudiante', 'Estudiante'),
    ]
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]

    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='confirmaciones_rite')
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    usuario = models.CharField(max_length=100, blank=True, default='', help_text='Usuario que registró la confirmación')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alumno} — {self.get_tipo_display()} — {self.cuatrimestre}° cuat."

    class Meta:
        verbose_name = "Confirmación de RITE"
        verbose_name_plural = "Confirmaciones de RITE"
        unique_together = ('alumno', 'cuatrimestre', 'tipo')
        ordering = ['cuatrimestre', 'tipo']


class PublicacionBoletin(models.Model):
    """Publicación anual del boletín (RITE) para los alumnos.

    Es la única fuente de verdad para que un alumno pueda ver su boletín.
    Mientras no esté publicado, el alumno solo ve su resumen "Mis notas".
    La habilita secretaría o el equipo directivo con un interruptor por año.
    """

    anio = models.PositiveIntegerField(unique=True, verbose_name="Año")
    publicado = models.BooleanField(default=False, verbose_name="Publicado")
    fecha_publicacion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de publicación"
    )
    usuario = models.CharField(
        max_length=100, blank=True, default='', verbose_name="Usuario"
    )

    def __str__(self):
        estado = "Publicado" if self.publicado else "Oculto"
        return f"Boletines {self.anio} — {estado}"

    class Meta:
        verbose_name = "Publicación de boletín"
        verbose_name_plural = "Publicaciones de boletines"
        ordering = ["-anio"]


# ─────────────────────────────────────────────
#  ENCABEZADO DE LA PLANILLA IMPRIMIBLE
# ─────────────────────────────────────────────

class PlanillaDatos(models.Model):
    """Datos de encabezado de la planilla imprimible (turno y preceptor/a).

    Se guardan por materia para no modificar las tablas compartidas de
    alumnos y docentes.
    """
    materia = models.OneToOneField(
        'docentes.Materia', on_delete=models.CASCADE, related_name='planilla_datos',
    )
    turno = models.CharField(max_length=50, blank=True, default='')
    preceptor = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"Datos de planilla — {self.materia}"

    class Meta:
        verbose_name = "Datos de planilla"
        verbose_name_plural = "Datos de planilla"