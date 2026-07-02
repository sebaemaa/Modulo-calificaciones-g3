from django.db import models #le decimos que de la libreria django.db nos importe models s la clase base para crear modelos


class AlumnoCalificacion(models.Model):# creamos una clase la cual se llama alumnoscalificacion lo cual esto basicamente seria una tabla model es la clase base para crear modelos
    nombre = models.CharField(max_length=100)#charfield (campo de texto corto) max de caracteres 100 
    curso = models.CharField(max_length=5)#charfield (campo de texto corto) max de caracteres 5
    division = models.CharField(max_length=2) #charfield (campo de texto corto) max de caracteres 2 
    materia = models.CharField(max_length=50) #charfield (campo de texto corto) max de caracteres 50 
    nota1 = models.DecimalField(max_digits=4, decimal_places=2) #creamos la variable nota1 
    #decimalfield (campo decimal) que pide un num decimal preciso
    #max digits da la cantidad maxima de numeros que se pueden ingresar 
    #decimal_places=2 te dice que 2 de esos 4 numeros son decimales es decir van despues de la coma
    #esto sirve ya que aveces las calificaciones no son numeros enteros sino que llevan coma 
    nota2 = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):#definidimos una funcion que pyhton reonoce por los guiones bajos
        # self representa esta calificacion en particula
        return f"{self.nombre} — {self.materia}"# desde self accedo a sus datos: alumno, materia
         # se va actualizando solo segun que calificacion se este mostrando


    class Meta:# cramos la clase meta adentro de la clase calificacion
        # Meta configura el comportamiento del modelo, no crea columnas en la tabla
        #es metadata (datos del modelo no del alumno)
        verbose_name = "Calificación de alumno"#le da un nombre legible para cuando se ingrese al panel de admin se vea mas "lindo y prolijo" (para UNA calificación)
        verbose_name_plural = "Calificaciones de alumnos"#lo mismo pero para cuando se muestran VARIAS calificaciones juntas
