import django.db.models.deletion  # Importa utilidades para manejar las relaciones entre tablas (como el borrado en cascada)
from django.db import migrations, models  # Importa las clases base para definir migraciones y los tipos de datos de los campos

class Migration(migrations.Migration):  # Define la clase de migración que Django ejecutará
    initial = True  # Marca esta migración como la base inicial de la aplicación

    dependencies = [  # Lista de otras migraciones necesarias antes de ejecutar esta
        ('alumnos', '0001_initial'),  # Debe existir la tabla de Alumnos primero
        ('docentes', '0001_initial'),  # Debe existir la tabla de Materias (en docentes) primero
    ]

    operations = [  # Lista de acciones que se aplicarán a la base de datos
        migrations.CreateModel(  # Instrucción para crear una nueva tabla
            name='Calificacion',  # Nombre de la tabla en la base de datos
            fields=[  # Definición de las columnas de la tabla
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),  # Llave primaria autoincremental
                ('periodo', models.CharField(choices=[('1B', '1° Bimestre'), ('2B', '2° Bimestre'), ('3B', '3° Bimestre'), ('4B', '4° Bimestre')], max_length=2)),  # Campo de texto limitado a opciones específicas
                ('nota', models.DecimalField(decimal_places=2, max_digits=4)),  # Campo numérico: máximo 99.99 (4 dígitos totales, 2 decimales)
                ('alumno', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calificaciones', to='alumnos.alumno')),  # Relación con Alumno: si se borra el alumno, se borran sus notas
                ('materia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calificaciones', to='docentes.materia')),  # Relación con Materia: si se borra la materia, se borran sus notas
            ],
            options={  # Configuración adicional del modelo
                'verbose_name': 'Calificación',  # Nombre legible en singular para el panel de administración
                'verbose_name_plural': 'Calificaciones',  # Nombre legible en plural para el panel de administración
                'ordering': ['alumno', 'materia', 'periodo'],  # Orden predeterminado al mostrar los registros
                'unique_together': {('alumno', 'materia', 'periodo')},  # Restricción: prohíbe duplicar la misma nota para un alumno en la misma materia y bimestre
            },
        ),
    ]
