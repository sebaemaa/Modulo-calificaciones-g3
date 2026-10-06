from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("alumnos", "0015_historialacademicoanual_alumno_promocion_estado"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="responsablealumno",
            name="activo",
        ),
    ]
