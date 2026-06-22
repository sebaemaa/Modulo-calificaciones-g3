from django.db import models  # Importa el módulo que permite definir modelos (tablas de BD) usando clases de Python

class Curso(models.Model):  # models.Model es la clase base: hace que Curso se convierta en una tabla SQL llamada "calificaciones_curso"
    año = models.IntegerField(verbose_name="Año lectivo")  # IntegerField → columna INTEGER en SQL. verbose_name es la etiqueta que Django usa en formularios y admin
    curso = models.CharField(max_length=5, verbose_name="Curso")  # CharField → VARCHAR(5) en SQL. max_length es obligatorio, define el límite de caracteres
    division = models.CharField(max_length=5, verbose_name="División")  # Otro VARCHAR(5) para la división (A, B, Única)
    materia = models.CharField(max_length=100, verbose_name="Materia")  # VARCHAR(100) para el nombre de la materia
    profesor = models.CharField(  # CharField con opciones extra
        max_length=200,  # Máximo 200 caracteres
        blank=True,  # blank=True permite el campo vacío en formularios Django
        null=True,  # null=True permite NULL en la base de datos SQL (no es lo mismo que blank)
        verbose_name="Nombre del profesor"
    )

    class Meta:  # Clase Meta: configuración interna del modelo, no crea columnas en la tabla
        verbose_name = "Curso"  # Cómo se muestra este modelo en singular en el admin de Django
        verbose_name_plural = "Cursos"  # Cómo se muestra en plural
        unique_together = ("año", "curso", "division", "materia")  # Crea una constraint UNIQUE(año, curso, division, materia) en SQL: evita que existan dos filas con la misma combinación
        ordering = ["-año", "curso", "division", "materia"]  # ORDER BY por defecto: año descendente (el - invierte), luego curso, division, materia ascendente

    def __str__(self):  # Método de Python: define qué devuelve str(obj). Django lo usa en admin, formularios, dropdowns
        return f"{self.curso} {self.division} - {self.materia} ({self.año})"  # f-string: interpola variables. Ejemplo: "1° A - Matemática (2026)"


class Alumno(models.Model):  # Esta clase crea la tabla SQL "calificaciones_alumno"
    nombre = models.CharField(max_length=200, verbose_name="Nombre completo")  # VARCHAR(200), NOT NULL implícito (es el default)
    dni = models.CharField(  # Campo de texto para el DNI
        max_length=20,
        verbose_name="DNI del alumno",
        null=True, blank=True,  # null=True → columna nullable en SQL; blank=True → campo opcional en formularios
        unique=True  # unique=True agrega UNIQUE CONSTRAINT en SQL: no pueden existir dos alumnos con el mismo DNI
    )
    curso = models.ForeignKey(  # ForeignKey: crea una columna curso_id en SQL que referencia a la tabla calificaciones_curso (clave foránea)
        Curso,  # Primer argumento: modelo al que apunta la FK
        on_delete=models.CASCADE,  # on_delete=models.CASCADE → genera ON DELETE CASCADE en SQL: si se borra el curso, se borran todos sus alumnos
        related_name="alumnos",  # related_name: permite acceder desde un objeto Curso a sus alumnos con curso.alumnos.all()
        verbose_name="Curso"
    )
    estado = models.CharField(  # Campo opcional para guardar TEA, TEP o TED
        max_length=20,
        blank=True, null=True,
        verbose_name="Estado manual (opcional)"
    )

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        unique_together = ("nombre", "curso")  # UNIQUE(nombre, curso_id): no permite dos alumnos con el mismo nombre en el mismo curso
        ordering = ["nombre"]  # ORDER BY nombre ASC

    def __str__(self):
        return f"{self.nombre} (DNI: {self.dni or '--'})"  # El operador 'or' devuelve '--' si self.dni es None o cadena vacía (falsy)


class Evaluacion(models.Model):  # Tabla "calificaciones_evaluacion": guarda cada nota individual de cada alumno en cada tipo de evaluación
    alumno = models.ForeignKey(  # FK a Alumno: columna alumno_id en SQL. Relación Muchos-a-Uno: un alumno tiene muchas evaluaciones
        Alumno, on_delete=models.CASCADE,
        related_name="evaluaciones",  # alumno.evaluaciones.all() devuelve todas las evaluaciones de ese alumno
        verbose_name="Alumno"
    )
    tipo = models.CharField(max_length=100, verbose_name="Tipo de evaluación")  # VARCHAR(100): "TP 1", "Examen", "Participación", etc.
    valor = models.DecimalField(  # DecimalField → DECIMAL(4,2) en SQL: número de hasta 4 dígitos totales, 2 después de la coma. Rango: -99.99 a 999.99
        max_digits=4,  # Cantidad máxima de dígitos (incluyendo decimales)
        decimal_places=2,  # Cantidad de dígitos después del punto decimal
        null=True, blank=True,  # nullable: permite que la nota esté vacía (alumno no calificado aún)
        verbose_name="Valor (0-10)"
    )

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        unique_together = ("alumno", "tipo")  # UNIQUE(alumno_id, tipo): evita que un alumno tenga dos evaluaciones del mismo tipo
        ordering = ["tipo"]  # ORDER BY tipo ASC

    def __str__(self):
        nota = self.valor if self.valor is not None else "--"  # Expresión ternaria: "valor si no es None, sino '--'"
        return f"{self.alumno.nombre} - {self.tipo}: {nota}"  # Formato legible: "Juan Pérez - TP 1: 8.50"


class Mensaje(models.Model):  # Tabla "calificaciones_mensaje": mensajes que el profesor envía a los alumnos de un curso
    curso = models.ForeignKey(  # FK a Curso: cada mensaje pertenece a un curso específico
        Curso, on_delete=models.CASCADE,
        related_name="mensajes",  # curso.mensajes.all() para obtener todos los mensajes de un curso
        verbose_name="Curso"
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")  # VARCHAR(200): asunto o título del mensaje
    contenido = models.TextField(verbose_name="Contenido")  # TextField → TEXT en SQL: sin límite de caracteres, para mensajes largos
    creado = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")  # DateTimeField → DATETIME en SQL. auto_now_add=True: Django inserta la fecha/hora actual automáticamente SOLO al crear (no se actualiza después)

    class Meta:
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ["-creado"]  # ORDER BY creado DESC: los más nuevos primero

    def __str__(self):
        return f"{self.curso} - {self.titulo}"  # Muestra "1° A - Matemática (2026) - Recordatorio examen"


class NotaDireccion(models.Model):  # Tabla "calificaciones_notadireccion": reportes que el profesor envía a dirección sobre un alumno específico
    alumno = models.ForeignKey(  # FK a Alumno: el alumno sobre el que se reporta
        Alumno, on_delete=models.CASCADE,
        related_name="notas_direccion",
        verbose_name="Alumno"
    )
    curso = models.ForeignKey(  # FK a Curso (redundante porque ya se puede obtener desde alumno.curso). Se guarda explícitamente para evitar hacer JOIN cada vez que se listan reportes de un curso
        Curso, on_delete=models.CASCADE,
        related_name="notas_direccion",
        verbose_name="Curso"
    )
    asunto = models.CharField(max_length=200, verbose_name="Asunto")  # VARCHAR(200): título/resumen del reporte
    mensaje = models.TextField(verbose_name="Mensaje")  # TEXT: cuerpo del reporte, sin límite de caracteres
    creado = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")  # DATETIME: se autogenera al crear el registro

    class Meta:
        verbose_name = "Nota a Dirección"
        verbose_name_plural = "Notas a Dirección"
        ordering = ["-creado"]  # Más recientes primero

    def __str__(self):
        return f"{self.alumno.nombre} - {self.asunto}"
