from django.db import models # estamos importando los modelos de django.db contiene todas las tablas para traducir el pyhton a base de datos

class AlumnoCalificacion(models.Model):
    alumno = models.ForeignKey( 'alumnos.Alumno',on_delete=models.CASCADE,related_name='alumno_calificaciones')
    #models.foreingkey quiere decir que esto se relaciona con otra tabla
    #'alumnos.Alumno' es el string que apunta al modelo Alumno de la app alumnos
    #on_delete =models.CASCADE lo que hace esto es que si se borra un alumno se borren todas sus calificaciones en cascada
    #related_name=calificaciones lo que hace es basicamente volver hacia atras es decir poder ir desde un alumno a sus calificaciones
    #porque el foreingkey lo que hace es ver desde calificaciones al alumno  
    materia = models.ForeignKey('docentes.Materia',on_delete=models.CASCADE,related_name='alumno_calificaciones')
    nota1 = models.DecimalField(max_digits=4, decimal_places=2) #creamos la variable nota1 
    #decimalfield basicamente lo que hace es decir que quiere un numero decimal preciso
    #max digits da la cantidad maxima de numeros que se pueden ingresar 
    #decimal_places=2 te dice que 2 de esos 4 numeros son decimales es decir van despues de la coma
    #esto sirve ya que aveces las calificaciones no son numeros enteros sino que llevan coma 
    nota2 = models.DecimalField(max_digits=4, decimal_places=2)
    

    def __str__(self):#definidimos una funcion que pyhton reonoce por los guiones bajos
        # self representa esta calificacion en particular
        return f"{self.alumno} — {self.materia}"# desde self accedo a sus datos: alumno, materia, periodo y nota
         # se va actualizando solo segun que calificacion se este mostrando

    class Meta: # cramos la clase meta adentro de la clase calificacion
        # Meta configura el comportamiento del modelo, no crea columnas en la tabla
        #es metadata (datos del modelo no del alumno)
        verbose_name = "Calificación de alumno"#le da un nombre legible para cuando se ingrese al panel de admin se vea mas "lindo y prolijo" (para UNA calificación)
        verbose_name_plural = "Calificaciones de alumnos"#lo mismo pero para cuando se muestran VARIAS calificaciones juntas
        unique_together = [('alumno', 'materia')]#el unique together hace que no puedan haber dos notas para el mismo alumno en el mismo periodo y materia
      