from django.contrib import admin

from .models import (
    Alumno,
    Curso,
    ExpedienteDocumento,
    HistorialAcademicoAnual,
    HistorialBajaAlumno,    
    HistorialPromocionAlumno,
    ObservacionAcademica,
    RegistroActividadAlumno,
    ResponsableAlumno,
    TutorAlumno,
)


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "dni", "anio", "division", "activo")
    list_filter = ("activo", "anio", "division", "tipo_identificacion")
    search_fields = ("apellido", "nombre", "dni")


admin.site.register(Curso)
admin.site.register(TutorAlumno)
admin.site.register(ResponsableAlumno)
admin.site.register(ExpedienteDocumento)
admin.site.register(HistorialAcademicoAnual)
admin.site.register(HistorialBajaAlumno)
admin.site.register(HistorialPromocionAlumno)
admin.site.register(ObservacionAcademica)
admin.site.register(RegistroActividadAlumno)