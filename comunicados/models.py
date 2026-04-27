from django.db import models

# ================================================================
# MÓDULO 5 — COMUNICADOS Y NOTIFICACIONES
# Grupo responsable: [nombre del grupo]
# ================================================================

DESTINATARIO_CHOICES = [
    ('TODOS', 'Todos'),
    ('DOCENTES', 'Docentes'),
    ('CURSO', 'Curso específico'),
]

class Comunicado(models.Model):
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    fecha = models.DateField(auto_now_add=True)
    destinatario = models.CharField(max_length=20, choices=DESTINATARIO_CHOICES, default='TODOS')
    curso = models.ForeignKey(
        'alumnos.Curso', on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Solo si el destinatario es un curso específico"
    )
    archivado = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Comunicado"
        verbose_name_plural = "Comunicados"
        ordering = ['-fecha']


class LecturaComunicado(models.Model):
    """Registra qué usuario leyó cada comunicado."""
    comunicado = models.ForeignKey(Comunicado, on_delete=models.CASCADE, related_name='lecturas')
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    fecha_lectura = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comunicado', 'usuario')
