import os
from datetime import datetime, timedelta

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models #impota el modelo de datos de django para crear las tablas en la base de datos


class Curso(models.Model):
    anio = models.IntegerField(verbose_name="Año")  # campo entero para el año del curso
    division = models.CharField(
        max_length=1, verbose_name="División"
    )  # campo de texto para la división del curso, limitado a un caracter

    def __str__(self):
        return f"{self.anio}° {self.division}"

    # Configuración extra del modelo
    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ["anio", "division"]


class TutorAlumno(models.Model):
    """Modelo legado.

    Se mantiene por compatibilidad temporal con datos existentes.
    El rediseño para "Padres / Tutores" se implementa en `ResponsableAlumno`.
    """

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    email = models.CharField(max_length=254, blank=True, default="")
    telefono = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Teléfono del tutor",
    )

    certificado_antivariolico = models.CharField(max_length=50, blank=True, default="")
    certificado_antidifterico = models.CharField(max_length=50, blank=True, default="")
    certificado_antipolio = models.CharField(max_length=50, blank=True, default="")
    certificado_buco_dental = models.CharField(max_length=50, blank=True, default="")

    nacionalidad = models.CharField(max_length=100, blank=True, default="")
    profesion = models.CharField(max_length=150, blank=True, default="")

    firma = models.FileField(
        upload_to="alumnos/tutores_firmas/",
        blank=True,
        null=True,
        verbose_name="Firma del padre o tutor",
    )

    anotaciones_particulares = models.TextField(blank=True, default="")
    n_orden = models.PositiveIntegerField(default=1)
    perimetral = models.CharField(max_length=100, blank=True, default="")
    puede_retirar = models.BooleanField(default=False)

    alumno = models.ForeignKey(
        "Alumno",
        on_delete=models.CASCADE,
        related_name="tutores",
    )

    class Meta:
        verbose_name = "Tutor / Padre (legado)"
        verbose_name_plural = "Tutores / Padres (legado)"
        ordering = ["n_orden", "apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (Orden {self.n_orden})"


class ResponsableAlumno(models.Model):
    class TipoResponsable(models.TextChoices):
        TUTOR_RESPONSABLE = "Tutor Responsable", "Tutor Responsable"
        TUTOR_SECUNDARIO = "Tutor Secundario", "Tutor Secundario"
        PADRE = "Padre", "Padre"
        MADRE = "Madre", "Madre"
        ABUELO = "Abuelo", "Abuelo"
        ABUELA = "Abuela", "Abuela"
        HERMANO = "Hermano", "Hermano"
        HERMANA = "Hermana", "Hermana"
        FAMILIAR = "Familiar", "Familiar"
        TUTOR_LEGAL = "Tutor Legal", "Tutor Legal"
        OTRO = "Otro Responsable", "Otro Responsable"

    alumno = models.ForeignKey(
        "Alumno",
        on_delete=models.CASCADE,
        related_name="responsables",
    )

    tipo_responsable = models.CharField(
        max_length=40,
        choices=TipoResponsable.choices,
    )

    # Datos del responsable
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()

    parentesco = models.CharField(max_length=120, blank=True, default="")

    telefono = models.CharField(max_length=50, blank=True, default="")
    telefono_alternativo = models.CharField(max_length=50, blank=True, default="")
    correo_electronico = models.EmailField(blank=True, default="")

    domicilio = models.CharField(max_length=200, blank=True, default="")
    localidad = models.CharField(max_length=120, blank=True, default="")
    provincia = models.CharField(max_length=120, blank=True, default="")
    codigo_postal = models.CharField(max_length=20, blank=True, default="")

    ocupacion = models.CharField(max_length=150, blank=True, default="")
    lugar_trabajo = models.CharField(max_length=200, blank=True, default="")

    # Datos que existían en el legacy TutorAlumno
    # (certificados / perimetrales / firmas / anotaciones)
    certificado_antivariolico = models.CharField(max_length=50, blank=True, default="")
    certificado_antidifterico = models.CharField(max_length=50, blank=True, default="")
    certificado_antipolio = models.CharField(max_length=50, blank=True, default="")
    certificado_buco_dental = models.CharField(max_length=50, blank=True, default="")

    nacionalidad = models.CharField(max_length=100, blank=True, default="")
    profesion = models.CharField(max_length=150, blank=True, default="")

    perimetral = models.CharField(max_length=100, blank=True, default="")
    perimetral_motivo = models.CharField(max_length=255, blank=True, default="")
    puede_retirar = models.BooleanField(default=False)

    firma = models.FileField(
        upload_to="alumnos/tutores_firmas/",
        blank=True,
        null=True,
        verbose_name="Firma del padre o tutor",
    )

    anotaciones_particulares = models.TextField(blank=True, default="")

    # Observaciones
    observaciones = models.TextField(blank=True, default="")

    # Orden visual / consistente
    n_orden = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Responsable"
        verbose_name_plural = "Responsables"
        ordering = ["n_orden", "apellido", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["alumno", "dni", "tipo_responsable"],
                name="unique_responsable_alumno_dni_tipo",
            )
        ]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} — {self.tipo_responsable}"


class Alumno(models.Model):
# Guarda la información básica de cada alumno,
# como sus datos personales y de contacto.

    DOCUMENTOS_REQUERIDOS = (
        {
            "key": "identidad",
            "label": "Documento de identidad / CUIL",
            "patterns": ("dni", "documento", "cuil"),
        },
        {
            "key": "partida",
            "label": "Partida de nacimiento",
            "patterns": ("partida", "nacimiento"),
        },
        {
            "key": "vacunas",
            "label": "Certificado de vacunas",
            "patterns": ("vacuna", "vacunas", "sanitario", "salud"),
        },
        {
            "key": "constancia",
            "label": "Constancia / ficha médica",
            "patterns": ("constancia", "regular", "ficha", "medica", "médica"),
        },
    )

    class TipoIdentificacion(models.TextChoices):
        DOCUMENTO = "documento", "Documento"
        CUIL_PROVISORIO = "cuil_provisorio", "CUIL provisorio (extranjero)"

    class EstadoPromocion(models.TextChoices):
        PROMOCIONADO = "promocionado", "Promocionado"
        NO_PROMOCIONADO = "no_promocionado", "No Promocionado"

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="DNI"
    )
    tipo_identificacion = models.CharField(
        max_length=20,
        choices=TipoIdentificacion.choices,
        default=TipoIdentificacion.DOCUMENTO,
        verbose_name="Método de identificación",
    )

    fecha_nacimiento = models.DateField(
        verbose_name="Fecha de nacimiento"
    )

    domicilio = models.CharField(
        max_length=200,
        blank=True
    )

    telefono_contacto = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Teléfono de contacto"
    )

    anio = models.IntegerField(verbose_name="Año")
    division = models.CharField(max_length=1, verbose_name="División")
    activo = models.BooleanField(default=True)
    estado_promocion = models.CharField(
        max_length=20,
        choices=EstadoPromocion.choices,
        default=EstadoPromocion.PROMOCIONADO,
        verbose_name="Estado de promoción",
    )
    motivo_no_promocion = models.CharField(max_length=255, blank=True, default="")
    fecha_baja = models.DateField(blank=True, null=True)
    motivo_baja = models.CharField(max_length=255, blank=True, default="")
    certificado_baja = models.CharField(max_length=300, blank=True, default="")
    documentacion = models.FileField(
        upload_to="alumnos/documentacion/",
        blank=True,
        null=True,
        verbose_name="Documentación"
    )

    @property
    def documentacion_archivos(self):
        if not self.pk:
            return []
        carpeta = os.path.join("alumnos", "documentacion", str(self.pk))
        if not default_storage.exists(carpeta):
            return []
        _, archivos = default_storage.listdir(carpeta)
        return sorted(archivos)

    @property
    def documentacion_archivos_detalle(self):
        if not self.pk:
            return []
        carpeta = os.path.join("alumnos", "documentacion", str(self.pk))
        if not default_storage.exists(carpeta):
            return []
        _, archivos = default_storage.listdir(carpeta)
        detalles = []
        for nombre in sorted(archivos):
            ruta = os.path.join(carpeta, nombre)
            if not default_storage.exists(ruta):
                continue
            ruta_real = default_storage.path(ruta)
            timestamp = os.path.getmtime(ruta_real) if os.path.exists(ruta_real) else None
            dt = datetime.fromtimestamp(timestamp) if timestamp is not None else datetime.now()
            fecha_obj = dt.date()
            hoy = datetime.now().date()
            ayer = hoy - timedelta(days=1)
            if fecha_obj == hoy:
                fecha_label = "Hoy"
            elif fecha_obj == ayer:
                fecha_label = "Ayer"
            else:
                fecha_label = dt.strftime("%d/%m/%Y")
            detalles.append(
                {
                    "nombre": nombre,
                    "ruta": ruta,
                    "fecha": fecha_obj.strftime("%Y-%m-%d"),
                    "hora": dt.strftime("%H:%M"),
                    "fecha_label": fecha_label,
                }
            )
        return sorted(detalles, key=lambda item: (item["fecha"], item["hora"]), reverse=True)

    @property
    def documentacion_archivos_grupos(self):
        grupos = []
        for archivo in self.documentacion_archivos_detalle:
            if not grupos or grupos[-1]["fecha_label"] != archivo["fecha_label"]:
                grupos.append({"fecha_label": archivo["fecha_label"], "archivos": []})
            grupos[-1]["archivos"].append(archivo)
        return grupos

    @property
    def documentacion_requerida_estado(self):
        archivos = self.documentacion_archivos
        archivos_lower = {archivo: archivo.lower() for archivo in archivos}
        estado = []

        for doc in self.DOCUMENTOS_REQUERIDOS:
            coincidencias = []
            for archivo in archivos:
                archivo_lower = archivos_lower[archivo]
                if any(pattern in archivo_lower for pattern in doc["patterns"]):
                    coincidencias.append(archivo)

            estado.append(
                {
                    "key": doc["key"],
                    "label": doc["label"],
                    "archivos": coincidencias,
                    "completo": len(coincidencias) > 0,
                }
            )

        return estado

    @property
    def documentacion_archivos_sin_categoria(self):
        archivos = self.documentacion_archivos
        archivos_lower = {archivo: archivo.lower() for archivo in archivos}
        archivos_asignados = set()

        for doc in self.DOCUMENTOS_REQUERIDOS:
            for archivo in archivos:
                archivo_lower = archivos_lower[archivo]
                if any(pattern in archivo_lower for pattern in doc["patterns"]):
                    archivos_asignados.add(archivo)

        return [archivo for archivo in archivos if archivo not in archivos_asignados]

    @property
    def documentacion_faltante(self):
        return [doc["label"] for doc in self.documentacion_requerida_estado if not doc["completo"]]

    @property
    def documentacion_completa(self):
        return len(self.documentacion_faltante) == 0

    @property
    def expediente_documentos_detalle(self):
        return list(self.expediente_documentos.order_by("-fecha_carga", "-id"))

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.anio}° {self.division})"

    # Guarda el año, la división y el estado del alumno (activo o inactivo).
    # str define cómo se mostrará el alumno en texto,
    # mostrando apellido, nombre y curso.
    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ["apellido", "nombre"]


class ExpedienteDocumento(models.Model):
    class TipoDocumento(models.TextChoices):
        CERTIFICADO_ESTUDIOS_PREVIOS = "certificado_estudios_previos", "Certificado de estudios previos"
        PARTIDA_NACIMIENTO = "partida_nacimiento", "Partida de nacimiento"
        ANALITICO_CALIFICACIONES = "analitico_calificaciones", "Analítico de calificaciones"
        CONSTANCIA_TITULO = "constancia_titulo", "Constancia / certificado de título"
        OTRO = "otro", "Otro"

    class EstadoDocumento(models.TextChoices):
        VIGENTE = "vigente", "Vigente"
        VENCIDO = "vencido", "Vencido"
        PENDIENTE_ACTUALIZACION = "pendiente_actualizacion", "Pendiente de actualización"

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="expediente_documentos",
    )
    nombre_documento = models.CharField(max_length=180)
    tipo_documento = models.CharField(max_length=60, choices=TipoDocumento.choices)
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=40,
        choices=EstadoDocumento.choices,
        default=EstadoDocumento.VIGENTE,
    )
    archivo = models.FileField(
        upload_to="alumnos/expediente_estudiante/",
        blank=True,
        null=True,
        verbose_name="Archivo adjunto",
    )
    observaciones = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Documento de expediente"
        verbose_name_plural = "Documentos de expediente"
        ordering = ["-fecha_carga", "-id"]

    def __str__(self):
        return f"{self.nombre_documento} — {self.alumno}"


class HistorialBajaAlumno(models.Model):
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_bajas",
    )
    anio_baja = models.IntegerField(verbose_name="Año de baja")
    fecha_baja = models.DateField(verbose_name="Fecha de baja")
    motivo_baja = models.CharField(max_length=255, blank=True, default="")
    certificado_baja = models.CharField(max_length=300, blank=True, default="")
    snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Baja histórica"
        verbose_name_plural = "Bajas históricas"
        ordering = ["-anio_baja", "-fecha_baja"]

    def __str__(self):
        alumno_txt = self.alumno.__str__() if self.alumno_id else "Alumno sin vínculo"
        return f"Bajas {self.anio_baja} - {alumno_txt}"


class HistorialPromocionAlumno(models.Model):
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_promociones",
    )
    ciclo_lectivo = models.IntegerField(verbose_name="Ciclo lectivo")
    fecha_promocion = models.DateField(verbose_name="Fecha de promoción")
    anio_origen = models.IntegerField(verbose_name="Año de origen")
    anio_destino = models.IntegerField(verbose_name="Año de destino")
    snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Promoción histórica"
        verbose_name_plural = "Promociones históricas"
        ordering = ["-ciclo_lectivo", "-fecha_promocion"]

    def __str__(self):
        alumno_txt = self.alumno.__str__() if self.alumno_id else "Alumno sin vínculo"
        return f"Promoción {self.ciclo_lectivo}: {self.anio_origen}° -> {self.anio_destino}° ({alumno_txt})"


class HistorialAcademicoAnual(models.Model):
    class EstadoPromocion(models.TextChoices):
        PROMOCIONADO = "promocionado", "Promocionado"
        NO_PROMOCIONADO = "no_promocionado", "No Promocionado"

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historiales_academicos_anuales",
    )
    anio_lectivo = models.IntegerField(verbose_name="Año lectivo")
    curso = models.IntegerField(verbose_name="Curso")
    division = models.CharField(max_length=1, verbose_name="División")
    estado_alumno = models.CharField(max_length=30, default="Activo", verbose_name="Estado del alumno")
    resultado_final = models.CharField(max_length=120, blank=True, default="")
    fecha_promocion = models.DateField(blank=True, null=True)
    fecha_baja = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, default="")
    estado_promocion = models.CharField(
        max_length=20,
        choices=EstadoPromocion.choices,
        default=EstadoPromocion.PROMOCIONADO,
        verbose_name="Estado de promoción",
    )
    motivo_no_promocion = models.CharField(max_length=255, blank=True, default="")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Historial académico anual"
        verbose_name_plural = "Historiales académicos anuales"
        ordering = ["-anio_lectivo", "-actualizado", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["alumno", "anio_lectivo"],
                name="unique_historial_academico_alumno_anio",
            )
        ]

    def __str__(self):
        alumno_txt = self.alumno.__str__() if self.alumno_id else "Alumno sin vínculo"
        return f"{self.anio_lectivo} - {alumno_txt}"


class ObservacionAcademica(models.Model):
    class Conducta(models.TextChoices):
        EXCELENTE = "excelente", "Excelente"
        BUENA = "buena", "Buena"
        REGULAR = "regular", "Regular"
        A_MEJORAR = "a_mejorar", "A mejorar"

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="observaciones_academicas",
    )
    periodo = models.CharField(max_length=2, blank=True, default="")
    conducta = models.CharField(
        max_length=20,
        choices=Conducta.choices,
        default=Conducta.BUENA,
    )
    observacion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observaciones_academicas_creadas",
    )

    class Meta:
        verbose_name = "Observación académica"
        verbose_name_plural = "Observaciones académicas"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.alumno} — {self.get_conducta_display()}"


class RegistroActividadAlumno(models.Model):
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="registros_actividad",
        null=True,
        blank=True,
    )
    correo_electronico = models.EmailField(blank=True, default="")
    entidad = models.CharField(max_length=120)
    objeto_id = models.CharField(max_length=50, blank=True, default="")
    accion = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, default="")
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de actividad del alumno"
        verbose_name_plural = "Registros de actividad de alumnos"
        ordering = ["-fecha_hora", "-id"]

    def __str__(self):
        return f"{self.entidad} - {self.accion}"