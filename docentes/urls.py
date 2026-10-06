from django.urls import path
from . import views

app_name = 'docentes'

urlpatterns = [
    # Docentes
    path('', views.index, name='index'),
    path('nuevo/', views.nuevo_docente, name='nuevo_docente'),
    path('<int:pk>/', views.detalle_docente, name='detalle_docente'),
    path('<int:pk>/editar/', views.editar_docente, name='editar_docente'),
    path('<int:pk>/baja/', views.baja_docente, name='baja_docente'),

    # Materias
    path('materias/', views.materias_list, name='materias_list'),
    path('materias/nueva/', views.nueva_materia, name='nueva_materia'),
    path('materias/<int:pk>/editar/', views.editar_materia, name='editar_materia'),

    # Horarios
    path('horarios/', views.horarios_index, name='horarios_index'),
    path('horarios/nuevo/', views.nuevo_horario, name='nuevo_horario'),
    path('horarios/curso/<int:curso_id>/', views.horario_curso, name='horario_curso'),
]
