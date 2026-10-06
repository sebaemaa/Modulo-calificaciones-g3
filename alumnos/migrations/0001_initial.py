
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
  # Esta es la primera migration creada para la app,
    # por eso initialTrue.

    initial = True
 # No depende de ninguna otra migration previa.
    dependencies = []

    operations = [ 
    # Crea el modelo Curso 
        migrations.CreateModel(
            name="Curso",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),  # Campo entero para el año del curso 
                ("anio", models.IntegerField(verbose_name="Año")), 
                   # División del curso, texto corto 
                ("division", models.CharField(max_length=10, verbose_name="División")),
            ],
            options={
                "verbose_name": "Curso",
                "verbose_name_plural": "Cursos",
                # Ordena por año y división al recuperar objetos 
                "ordering": ["anio", "division"],
            },
        ), # Crea el modelo Alumno con sus campos y una relacion foreign key a curso
        migrations.CreateModel(
            name="Alumno",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ), # Nombre del alumno 
                ("nombre", models.CharField(max_length=100)),
                 # Apellido del alumno
                ("apellido", models.CharField(max_length=100)),
                  # DNI único por alumno
                (
                    "dni",
                    models.CharField(max_length=20, unique=True, verbose_name="DNI"),
                ),  # Fecha de nacimiento como DateField
                (
                    "fecha_nacimiento",
                    models.DateField(verbose_name="Fecha de nacimiento"),
                ),   # Domicilio opcional
                ("domicilio", models.CharField(blank=True, max_length=200)),
                (
                    "telefono_contacto",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="Teléfono de contacto"
                    ),
                ),  # Marca si el alumno está activo
                ("activo", models.BooleanField(default=True)), 
                 # Relación con Curso usando foreign key con protección
                (
                    "curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="alumnos",
                        to="alumnos.curso",
                    ),
                ),
            ],
            options={
                "verbose_name": "Alumno",
                "verbose_name_plural": "Alumnos",
                "ordering": ["apellido", "nombre"],
            },
        ),
    ]
