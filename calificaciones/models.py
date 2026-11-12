"""Modelos del Módulo 3 — Gestión de Calificaciones.

Se guardan las notas por categoría de evaluación, el cierre de cada
cuatrimestre (valoración RITE, notas de diciembre/febrero y final), las
inasistencias por materia y la publicación anual del boletín.

El módulo consulta las tablas de alumnos y docentes, pero no las modifica:
los datos propios de la planilla viven acá.
"""
# Trae las herramientas de Django para definir tablas (cada clase = una tabla).
from django.db import models

# ================================================================
# MÓDULO 3 — GESTIÓN DE CALIFICACIONES
# Grupo responsable: Grupo 3
# Consulta tablas de: alumnos, docentes
# ================================================================

# ─────────────────────────────────────────────
#  CALIFICACIONES POR PERÍODO (registro simple)
# ─────────────────────────────────────────────

# Opciones del campo "periodo": (valor que se guarda, texto que se muestra).
PERIODO_CHOICES = [
    ('1B', '1° Bimestre'),
    ('2B', '2° Bimestre'),
    ('3B', '3° Bimestre'),
    ('4B', '4° Bimestre'),
]


# Tabla vieja del esqueleto del profesor: una nota por bimestre. No se usa en pantallas.
class Calificacion(models.Model):
    """Calificación por bimestre del esqueleto original.

    No la usa ninguna pantalla del módulo: queda para no romper el esqueleto
    que armó el profesor (su tabla ya existe en la base).
    """
    # FK = "este registro pertenece a un alumno". CASCADE: si se borra el alumno, se borran sus notas.
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='calificaciones')
    # FK a la materia. related_name permite hacer materia.calificaciones.all().
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='calificaciones')
    # Texto de 2 letras limitado a las opciones de arriba (1B..4B).
    periodo = models.CharField(max_length=2, choices=PERIODO_CHOICES)
    # Numero decimal: hasta 4 digitos, 2 de ellos decimales (ej. 10.00).
    nota = models.DecimalField(max_digits=4, decimal_places=2)

    # Como se muestra el registro en el admin o al imprimirlo.
    def __str__(self):
        # get_periodo_display() devuelve el texto lindo ("1° Bimestre") en vez de "1B".
        return f"{self.alumno} — {self.materia} — {self.get_periodo_display()}: {self.nota}"

    # Meta = configuracion de la tabla (no son columnas).
    class Meta:
        # Nombre en singular y plural que muestra el admin.
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        # No puede haber dos notas del mismo alumno, materia y periodo.
        unique_together = ('alumno', 'materia', 'periodo')
        # Orden por defecto al listar.
        ordering = ['alumno', 'materia', 'periodo']


# Tabla: cada columna de la grilla de notas (TP, Examen, etc.) de una materia.
class CategoriaEvaluacion(models.Model):
    """Columna de la grilla de notas (TP, examen, participación...).

    El campo ``grupo`` permite que varias columnas sumen un mismo peso y el
    campo ``peso`` define cuánto aporta a la calificación del cuatrimestre.
    """
    # Nombre de la columna. help_text es la ayuda que aparece en el formulario.
    nombre = models.CharField(max_length=100, help_text="Ej: Trabajo Práctico, Examen, Participación")
    # A que materia pertenece la categoria.
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='categorias')
    # Numero entero >= 0 para ordenar las columnas en la grilla.
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la grilla")
    # Grupo opcional (blank=True permite dejarlo vacio): junta varias columnas bajo un titulo.
    grupo = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Agrupa columnas en la planilla (ej: Trabajos prácticos)",
    )
    # Porcentaje que pesa en la nota del cuatrimestre. null=True: puede no tener peso.
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="% que aporta la categoría a la calificación (ej: 30)",
    )

    # Texto con el que se muestra la categoria.
    def __str__(self):
        return f"{self.nombre} — {self.materia}"

    # Configuracion de la tabla.
    class Meta:
        verbose_name = "Categoría de evaluación"
        verbose_name_plural = "Categorías de evaluación"
        # Se listan por materia, despues por orden y despues por nombre.
        ordering = ['materia', 'orden', 'nombre']


# Tabla: UNA nota de UN alumno en UNA categoria y cuatrimestre. Es lo que carga el docente.
class NotaEvaluacion(models.Model):
    """Nota de un alumno en una categoría y cuatrimestre."""
    # Opciones de cuatrimestre: se guarda 1 o 2.
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]

    # De que alumno es la nota.
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='notas_evaluacion')
    # De que materia.
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='notas_evaluacion')
    # En que columna (categoria) va. Si se borra la categoria, se borran sus notas.
    categoria = models.ForeignKey(CategoriaEvaluacion, on_delete=models.CASCADE, related_name='notas')
    # Cuatrimestre: 1 o 2.
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES)
    # La nota en si, con un decimal (ej. 7.5).
    valor = models.DecimalField(max_digits=4, decimal_places=1)
    # Descripcion opcional de la evaluacion.
    descripcion = models.CharField(max_length=200, blank=True, help_text="Ej: Primer parcial, TP N°3")
    # Fecha opcional de la evaluacion.
    fecha = models.DateField(null=True, blank=True)

    # Texto con el que se muestra la nota.
    def __str__(self):
        return f"{self.alumno} - {self.categoria.nombre}: {self.valor}"

    # Nombres para el admin.
    class Meta:
        verbose_name = "Nota de evaluación"
        verbose_name_plural = "Notas de evaluación"


# Tabla vieja de configuracion del boletin. Ya no se usa; queda para no perder datos.
class BoletinConfig(models.Model):
    """Configuración vieja por cuatrimestre (una sola para toda la escuela).

    Ya no la usa ninguna pantalla: la fecha de cierre ahora se guarda por
    materia en ``CierreCuatrimestre.fecha_cierre`` y la publicación del
    boletín es anual (``PublicacionBoletin``). Queda para no perder datos.
    """
    # Opciones de cuatrimestre.
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]

    # unique=True: solo una configuracion por cuatrimestre.
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES, unique=True)
    # Si el boletin estaba publicado o no (verdadero/falso).
    publicado = models.BooleanField(default=False)
    # Cuando se publico (fecha y hora).
    fecha_publicacion = models.DateTimeField(null=True, blank=True)

    # Texto con el que se muestra.
    def __str__(self):
        # Operador ternario: "Publicado" si publicado es True, si no "Oculto".
        estado = "Publicado" if self.publicado else "Oculto"
        return f"Boletín {self.get_cuatrimestre_display()} — {estado}"

    # Nombres para el admin.
    class Meta:
        verbose_name = "Configuración de boletín"
        verbose_name_plural = "Configuraciones de boletines"


# ─────────────────────────────────────────────
#  CIERRE DEL CUATRIMESTRE Y ASISTENCIA
# ─────────────────────────────────────────────

# Tabla CLAVE: el "cierre" de un alumno en una materia y cuatrimestre (valoracion, nota oficial, etc.).
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
    # Constantes con los 3 codigos de valoracion RITE, para no escribir los textos a mano.
    TEA = 'TEA'
    TEP = 'TEP'
    TED = 'TED'
    # Opciones de valoracion: codigo que se guarda y su significado.
    VALORACION_CHOICES = [
        (TEA, 'Trayectoria Educativa Avanzada'),
        (TEP, 'Trayectoria Educativa en Proceso'),
        (TED, 'Trayectoria Educativa Discontinua'),
    ]
    # Opciones de cuatrimestre.
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]
    # Opciones de cursada: C = cursa por primera vez, R = recursa.
    CURSADA_CHOICES = [
        ('C', 'Cursa por primera vez'),
        ('R', 'Recursa'),
    ]

    # De que alumno es el cierre.
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='cierres_cuatrimestre')
    # De que materia.
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='cierres_cuatrimestre')
    # De que cuatrimestre (1 o 2).
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES)
    # Cursada: una letra, por defecto 'C'.
    cursada = models.CharField(
        max_length=1, choices=CURSADA_CHOICES, default='C',
        help_text='C: cursa por primera vez · R: recursa',
    )
    # Valoracion TEA/TEP/TED que elige el docente. Puede quedar vacia.
    valoracion_preliminar = models.CharField(max_length=3, choices=VALORACION_CHOICES, blank=True, default='')
    # Nota oficial del cuatrimestre (se guarda al cerrar). Puede estar vacia.
    calificacion = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    # Marca si el alumno tiene que intensificar (recuperar) el cuatrimestre.
    intensificacion = models.BooleanField(default=False, help_text='Necesita intensificación en el cuatrimestre')
    # Nota de la mesa de diciembre (opcional).
    nota_diciembre = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    # Nota de la mesa de febrero (opcional).
    nota_febrero = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    # Nota final (su significado cambia segun el cuatrimestre, ver el texto de arriba).
    calificacion_final = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    # True cuando el docente cerro el cuatrimestre: ya no se pueden editar las notas.
    cerrado = models.BooleanField(default=False)
    # Fecha y hora en que se cerro.
    fecha_cierre = models.DateTimeField(null=True, blank=True, help_text='Cuándo el docente cerró el cuatrimestre')

    # Texto con el que se muestra.
    def __str__(self):
        # Si no tiene valoracion muestra "sin valorar".
        valoracion = self.valoracion_preliminar or 'sin valorar'
        return f"{self.alumno} — {self.materia} — {self.cuatrimestre}° cuat.: {valoracion}"

    # Configuracion de la tabla.
    class Meta:
        verbose_name = "Cierre de cuatrimestre"
        verbose_name_plural = "Cierres de cuatrimestre"
        # Un solo cierre por alumno + materia + cuatrimestre.
        unique_together = ('alumno', 'materia', 'cuatrimestre')
        # Orden por defecto.
        ordering = ['materia', 'alumno']


# Tabla: faltas de un alumno en una materia y cuatrimestre, cargadas a mano por el docente.
class InasistenciaMateria(models.Model):
    """Inasistencias de un alumno en una materia para un cuatrimestre.

    El docente las puede cargar desde "Cargar notas" o desde la planilla.
    Si no hay carga manual, la planilla y el boletín leen el módulo Asistencia.
    Se usa un campo Decimal para permitir medias faltas (tardanzas = 0,5).
    """
    # Opciones de cuatrimestre.
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]

    # De que alumno.
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='inasistencias_materia')
    # De que materia.
    materia = models.ForeignKey('docentes.Materia', on_delete=models.CASCADE, related_name='inasistencias_materia')
    # De que cuatrimestre.
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES)
    # Cantidad de faltas; decimal para permitir medias faltas (0,5).
    cantidad = models.DecimalField(max_digits=5, decimal_places=1, default=0, help_text="Cantidad de inasistencias (0,5 = media falta)")

    # Texto con el que se muestra.
    def __str__(self):
        return f"{self.alumno} — {self.materia} — {self.cuatrimestre}° cuat.: {self.cantidad} inasist."

    # Configuracion de la tabla.
    class Meta:
        verbose_name = "Inasistencia por materia"
        verbose_name_plural = "Inasistencias por materia"
        # Un solo registro por alumno + materia + cuatrimestre.
        unique_together = ('alumno', 'materia', 'cuatrimestre')
        ordering = ['materia', 'alumno']


# ─────────────────────────────────────────────
#  BOLETÍN (RITE) Y PUBLICACIÓN ANUAL
# ─────────────────────────────────────────────

# Tabla: las "firmas" digitales del boletin (quien lo vio y cuando).
class ConfirmacionRite(models.Model):
    """Quién tomó conocimiento del RITE (boletín) y cuándo.

    El sistema guarda quién y cuándo, como dice la leyenda del RITE.
    """
    # Quien puede firmar: director, adulto responsable o estudiante.
    TIPO_CHOICES = [
        ('director', 'Director/a'),
        ('adulto', 'Adulta/o responsable'),
        ('estudiante', 'Estudiante'),
    ]
    # Opciones de cuatrimestre.
    CUATRIMESTRE_CHOICES = [(1, '1° Cuatrimestre'), (2, '2° Cuatrimestre')]

    # De que alumno es el boletin firmado.
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='confirmaciones_rite')
    # De que cuatrimestre.
    cuatrimestre = models.IntegerField(choices=CUATRIMESTRE_CHOICES)
    # Que tipo de firmante es (una de las 3 opciones).
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    # Nombre del usuario que hizo clic en firmar.
    usuario = models.CharField(max_length=100, blank=True, default='', help_text='Usuario que registró la confirmación')
    # auto_now_add: Django pone sola la fecha y hora al crear el registro.
    fecha = models.DateTimeField(auto_now_add=True)

    # Texto con el que se muestra.
    def __str__(self):
        return f"{self.alumno} — {self.get_tipo_display()} — {self.cuatrimestre}° cuat."

    # Configuracion de la tabla.
    class Meta:
        verbose_name = "Confirmación de RITE"
        verbose_name_plural = "Confirmaciones de RITE"
        # Cada tipo de firmante firma una sola vez por alumno y cuatrimestre.
        unique_together = ('alumno', 'cuatrimestre', 'tipo')
        ordering = ['cuatrimestre', 'tipo']


# Tabla: el interruptor que publica los boletines de un año para los alumnos.
class PublicacionBoletin(models.Model):
    """Publicación anual del boletín (RITE) para los alumnos.

    Es la única fuente de verdad para que un alumno pueda ver su boletín.
    Mientras no esté publicado, el alumno solo ve su resumen "Mis notas".
    La habilita secretaría o el equipo directivo con un interruptor por año.
    """

    # Año lectivo; unique: un solo registro por año.
    anio = models.PositiveIntegerField(unique=True, verbose_name="Año")
    # True = los alumnos ya pueden ver su boletin.
    publicado = models.BooleanField(default=False, verbose_name="Publicado")
    # Cuando se publico.
    fecha_publicacion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de publicación"
    )
    # Quien lo publico.
    usuario = models.CharField(
        max_length=100, blank=True, default='', verbose_name="Usuario"
    )

    # Texto con el que se muestra.
    def __str__(self):
        estado = "Publicado" if self.publicado else "Oculto"
        return f"Boletines {self.anio} — {estado}"

    # Configuracion de la tabla.
    class Meta:
        verbose_name = "Publicación de boletín"
        verbose_name_plural = "Publicaciones de boletines"
        # El "-" ordena de mayor a menor: el año mas nuevo primero.
        ordering = ["-anio"]


# ─────────────────────────────────────────────
#  ENCABEZADO DE LA PLANILLA IMPRIMIBLE
# ─────────────────────────────────────────────

# Tabla: datos del encabezado de la planilla impresa (turno y preceptor) por materia.
class PlanillaDatos(models.Model):
    """Datos de encabezado de la planilla imprimible (turno y preceptor/a).

    Se guardan por materia para no modificar las tablas compartidas de
    alumnos y docentes.
    """
    # OneToOne: cada materia tiene como mucho UN registro de estos.
    materia = models.OneToOneField(
        'docentes.Materia', on_delete=models.CASCADE, related_name='planilla_datos',
    )
    # Turno (texto libre, puede quedar vacio).
    turno = models.CharField(max_length=50, blank=True, default='')
    # Nombre del preceptor/a.
    preceptor = models.CharField(max_length=100, blank=True, default='')

    # Texto con el que se muestra.
    def __str__(self):
        return f"Datos de planilla — {self.materia}"

    # Nombres para el admin.
    class Meta:
        verbose_name = "Datos de planilla"
        verbose_name_plural = "Datos de planilla"