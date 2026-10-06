from django import forms
from .models import Comunicado

# Formulario basado en el modelo Comunicado
class ComunicadoForm(forms.ModelForm):

    # Configuración de los campos que utiliza el formulario
    class Meta:

        # Modelo relacionado con este formulario
        model = Comunicado

        # Campos que aparecerán en el formulario de creación
        fields = [
            "titulo",
            "contenido",
            "destinatario",
            "curso",
            "archivo_pdf"
        ]

    # Personalización del formulario al inicializarse
    def __init__(self, *args, **kwargs):

        # Ejecuta la configuración original del ModelForm
        super().__init__(*args, **kwargs)

        # Permite crear comunicados sin seleccionar un curso
        self.fields["curso"].required = False

        # Cambia el nombre visible del campo en pantalla
        self.fields["curso"].label = "Curso específico"

        # Agrega estilos Bootstrap al selector de curso
        self.fields["curso"].widget.attrs.update({
            "class": "form-control"
        })

        # Agrega estilos Bootstrap al campo título
        self.fields["titulo"].widget.attrs.update({
            "class": "form-control"
        })

        # Agrega estilos y tamaño al campo contenido
        self.fields["contenido"].widget.attrs.update({
            "class": "form-control",
            "rows": 5
        })

        # Agrega estilo de selector Bootstrap al destinatario
        self.fields["destinatario"].widget.attrs.update({
            "class": "form-select"
        })

        # Agrega estilo Bootstrap al campo de archivo PDF
        self.fields["archivo_pdf"].widget.attrs.update({
            "class": "form-control"
        })