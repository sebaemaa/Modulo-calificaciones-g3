from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('alumnos/', include('alumnos.urls')),
    path('asistencia/', include('asistencia.urls')),
    path('calificaciones/', include('calificaciones.urls')),
    path('docentes/', include('docentes.urls')),
    path('comunicados/', include('comunicados.urls')),
]
