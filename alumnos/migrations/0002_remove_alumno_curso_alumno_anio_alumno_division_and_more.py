
from django.db import migrations, models


class Migration(migrations.Migration):
 # Esta migration depende de la inicial de la app alumnos
    dependencies = [
        ("alumnos", "0001_initial"),
    ]

    operations = [ 
# Quita el campo de relación ForeignKey curso en Alumno
        migrations.RemoveField(
            model_name="alumno",
            name="curso",
        ),  #Agrega un campo entero anio al modelo Alumno
        migrations.AddField(
            model_name="alumno",
            name="anio",
            field=models.IntegerField(default=1, verbose_name="Año"),
            preserve_default=False,
        ), #Agrega un campo texto division al modelo Alumno
        migrations.AddField(
            model_name="alumno",
            name="division",
            field=models.CharField(default=1, max_length=1, verbose_name="División"),
            preserve_default=False,
        ),  # Modifica el campo Cursodivision para limitarlo a 1 carácter
        migrations.AlterField(
            model_name="curso",
            name="division",
            field=models.CharField(max_length=1, verbose_name="División"),
        ),
    ]
