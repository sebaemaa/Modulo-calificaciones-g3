
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calificaciones', '0009_cierrecuatrimestre_fecha_cierre'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InasistenciaMateria',
        ),
    ]
