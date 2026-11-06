from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from cuentas.views import despues_del_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/profile/', despues_del_login, name='post_login'),
    path('', include('core.urls')),
    path('alumnos/', include('alumnos.urls')),
    path('asistencia/', include('asistencia.urls')),
    path('calificaciones/', include('calificaciones.urls')),
    path('docentes/', include('docentes.urls')),
    path('comunicados/', include('comunicados.urls')),
]
