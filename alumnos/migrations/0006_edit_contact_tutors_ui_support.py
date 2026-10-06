from django.db import migrations


class Migration(migrations.Migration):
    # Migración vacía para UI.
    # La conectamos a la 0005 para evitar ramas/hojas conflictivas en el grafo.
    dependencies = [
        ('alumnos', '0005_add_contact_fields_tutoralumno_and_email'),
    ]
    operations = []




