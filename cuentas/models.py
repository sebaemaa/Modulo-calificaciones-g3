from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Perfil(models.Model):
    """Vincula un usuario de Django con su rol y con su ficha real.

    Este modelo es del esqueleto: lo administra el docente.
    Los modulos lo CONSULTAN, no lo modifican.
    """

    ADMINISTRATIVO = 'administrativo'
    DIRECTIVO = 'directivo'
    DOCENTE = 'docente'
    ALUMNO = 'alumno'

    ROL_CHOICES = [
        (ADMINISTRATIVO, 'Personal administrativo'),
        (DIRECTIVO, 'Personal directivo'),
        (DOCENTE, 'Docente'),
        (ALUMNO, 'Alumno / Familia'),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)

    docente = models.OneToOneField(
        'docentes.Docente',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cuenta',
        help_text="Solo para usuarios con rol Docente",
    )
    alumno = models.OneToOneField(
        'alumnos.Alumno',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cuenta',
        help_text="Solo para usuarios con rol Alumno",
    )

    def clean(self):
        if self.rol == self.DOCENTE and self.docente is None:
            raise ValidationError("Un perfil con rol Docente debe apuntar a una ficha de docente.")
        if self.rol == self.ALUMNO and self.alumno is None:
            raise ValidationError("Un perfil con rol Alumno debe apuntar a una ficha de alumno.")
        if self.rol != self.DOCENTE and self.docente is not None:
            raise ValidationError("Solo un perfil con rol Docente puede apuntar a una ficha de docente.")
        if self.rol != self.ALUMNO and self.alumno is not None:
            raise ValidationError("Solo un perfil con rol Alumno puede apuntar a una ficha de alumno.")

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"
        ordering = ['usuario__username']
