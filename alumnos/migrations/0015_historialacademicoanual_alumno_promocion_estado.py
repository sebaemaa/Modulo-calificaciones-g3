from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("alumnos", "0014_registroactividadalumno"),
    ]

    operations = [
        migrations.AddField(
            model_name="alumno",
            name="estado_promocion",
            field=models.CharField(
                choices=[
                    ("promocionado", "Promocionado"),
                    ("no_promocionado", "No Promocionado"),
                ],
                default="promocionado",
                max_length=20,
                verbose_name="Estado de promoción",
            ),
        ),
        migrations.AddField(
            model_name="alumno",
            name="motivo_no_promocion",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.CreateModel(
            name="HistorialAcademicoAnual",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anio_lectivo", models.IntegerField(verbose_name="Año lectivo")),
                ("curso", models.IntegerField(verbose_name="Curso")),
                ("division", models.CharField(max_length=1, verbose_name="División")),
                ("estado_alumno", models.CharField(default="Activo", max_length=30, verbose_name="Estado del alumno")),
                ("resultado_final", models.CharField(blank=True, default="", max_length=120)),
                ("fecha_promocion", models.DateField(blank=True, null=True)),
                ("fecha_baja", models.DateField(blank=True, null=True)),
                ("observaciones", models.TextField(blank=True, default="")),
                (
                    "estado_promocion",
                    models.CharField(
                        choices=[
                            ("promocionado", "Promocionado"),
                            ("no_promocionado", "No Promocionado"),
                        ],
                        default="promocionado",
                        max_length=20,
                        verbose_name="Estado de promoción",
                    ),
                ),
                ("motivo_no_promocion", models.CharField(blank=True, default="", max_length=255)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                (
                    "alumno",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="historiales_academicos_anuales",
                        to="alumnos.alumno",
                    ),
                ),
            ],
            options={
                "verbose_name": "Historial académico anual",
                "verbose_name_plural": "Historiales académicos anuales",
                "ordering": ["-anio_lectivo", "-actualizado", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="historialacademicoanual",
            constraint=models.UniqueConstraint(
                fields=("alumno", "anio_lectivo"),
                name="unique_historial_academico_alumno_anio",
            ),
        ),
    ]
