from django.urls import path
from . import views

app_name = 'comunicados'

urlpatterns = [
    path('', views.index, name='index'),
]
