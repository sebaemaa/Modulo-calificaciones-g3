from django.apps import AppConfig  # Importa la clase base 'AppConfig' que Django utiliza para gestionar la configuración de las apps.

class CalificacionesConfig(AppConfig):  # Define una clase propia para tu configuración, heredando de la clase base.
    name = 'calificaciones'  # Indica a Django el nombre de la carpeta (o paquete) donde vive esta aplicación.