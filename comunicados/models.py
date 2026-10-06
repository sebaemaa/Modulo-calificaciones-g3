from django.db import models
from django.contrib.auth.models import User

# ================================================================
# MÓDULO 5 — COMUNICADOS Y NOTIFICACIONES
# ================================================================

# Opciones disponibles para indicar a quién va dirigido el comunicado
DESTINATARIO_CHOICES = [
    ('TODOS', 'Todos'),
    ('DOCENTES', 'Docentes'),
    ('CURSO', 'Curso específico'),
]

# Modelo principal que representa un comunicado publicado
class Comunicado(models.Model):

    # Título del comunicado
    titulo = models.CharField(
        max_length=200
    )

    # Texto o mensaje del comunicado
    contenido = models.TextField()

    # Guarda automáticamente la fecha de creación
    fecha = models.DateField(
        auto_now_add=True
    )

    # Indica el grupo al que está destinado el comunicado
    destinatario = models.CharField(
        max_length=20,
        choices=DESTINATARIO_CHOICES,
        default='TODOS'
    )

    # Relaciona el comunicado con un curso específico
    # Puede estar vacío si el destinatario no es un curso
    curso = models.ForeignKey(
        'alumnos.Curso',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Indica si el comunicado fue archivado globalmente
    archivado = models.BooleanField(
        default=False
    )

    # Permite adjuntar un archivo PDF al comunicado
    archivo_pdf = models.FileField(
        upload_to='comunicados_pdf/',
        null=True,
        blank=True
    )

    # Guarda el usuario que creó el comunicado
    autor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comunicados_creados',
        null=True
    )

    # Define cómo se muestra el objeto en Django
    def __str__(self):
        return self.titulo

    # Configuración adicional del modelo
    class Meta:

        # Nombre mostrado en el administrador
        verbose_name = "Comunicado"

        # Nombre plural mostrado en el administrador
        verbose_name_plural = "Comunicados"

        # Ordena los comunicados del más reciente al más antiguo
        ordering = ['-fecha']

# Registro de lecturas

# Modelo que registra qué usuarios leyeron un comunicado
class LecturaComunicado(models.Model):

    # Comunicado que fue leído
    comunicado = models.ForeignKey(
        Comunicado,
        on_delete=models.CASCADE,
        related_name='lecturas'
    )

    # Usuario que realizó la lectura
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # Fecha y hora en la que fue leído
    fecha_lectura = models.DateTimeField(
        auto_now_add=True
    )

    # Evita que un usuario registre varias lecturas del mismo comunicado
    class Meta:
        unique_together = ('comunicado', 'usuario')


    # Muestra información de la lectura
    def __str__(self):
        return f"{self.usuario} leyó {self.comunicado}"

# Estado del comunicado para cada usuario

# Guarda acciones personales de cada usuario sobre un comunicado
class EstadoComunicado(models.Model):

    # Usuario al que pertenece este estado
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # Comunicado asociado al estado
    comunicado = models.ForeignKey(
        Comunicado,
        on_delete=models.CASCADE
    )

    # Indica si el usuario archivó ese comunicado
    archivado = models.BooleanField(
        default=False
    )

    # Indica si el usuario ocultó/eliminó ese comunicado de su vista
    eliminado = models.BooleanField(
        default=False
    )

    # Evita duplicar estados del mismo usuario para el mismo comunicado
    class Meta:
        unique_together = ('usuario', 'comunicado')

    # Muestra el usuario y comunicado relacionado
    def __str__(self):
        return f"{self.usuario} - {self.comunicado}"