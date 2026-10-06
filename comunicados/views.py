from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from django.contrib.auth.models import User

from .models import Comunicado, EstadoComunicado, LecturaComunicado
from .forms import ComunicadoForm

# Obtener usuario alumno

# Obtiene el usuario actual o crea uno de prueba si no hay sesión iniciada
def obtener_usuario_alumno(request):

    # Si existe un usuario autenticado devuelve ese usuario
    if request.user.is_authenticated:
        return request.user

    # Crea un usuario temporal para pruebas del módulo
    usuario, creado = User.objects.get_or_create(
        username="alumno_demo"
    )
    return usuario

# PANTALLA PRINCIPAL

# Muestra la pantalla inicial donde se elige el tipo de acceso
def index(request):

    return render(
        request,
        "comunicados/index.html"
    )

# PANEL DIRECTIVO

# Permite crear y visualizar comunicados como directivo
def directivo(request):

    # Verifica si se envió el formulario de creación
    if request.method == "POST":

        # Carga los datos del formulario y archivos adjuntos
        form = ComunicadoForm(
            request.POST,
            request.FILES
        )

        # Comprueba que los datos sean válidos
        if form.is_valid():

            # Guarda el comunicado sin enviarlo todavía a la base de datos
            comunicado = form.save(
                commit=False
            )

            # Asigna como autor al usuario conectado
            if request.user.is_authenticated:
                comunicado.autor = request.user

            # Guarda finalmente el comunicado
            comunicado.save()

            # Vuelve al panel directivo
            return redirect(
                "comunicados:directivo"
            )

    else:

        # Carga un formulario vacío para crear comunicados
        form = ComunicadoForm()

    # Obtiene todos los comunicados existentes
    comunicados = Comunicado.objects.all()


    # Envía los datos al template del panel directivo
    return render(
        request,
        "comunicados/directivo.html",
        {
            "form": form,
            "comunicados": comunicados
        }
    )

# PANEL ALUMNO

# Muestra los comunicados disponibles para un alumno
def alumno(request):

    # Obtiene comunicados que no fueron archivados globalmente
    comunicados = Comunicado.objects.filter(
        archivado=False
    )

    # Si hay un usuario conectado aplica sus estados personales
    if request.user.is_authenticated:

        visibles = []


        # Revisa cada comunicado para ese usuario
        for comunicado in comunicados:

            # Crea o busca el estado personal del alumno
            estado, creado = EstadoComunicado.objects.get_or_create(
                usuario=request.user,
                comunicado=comunicado
            )

            # Solo muestra comunicados no archivados ni eliminados
            if not estado.eliminado and not estado.archivado:

                visibles.append(comunicado)

        # Actualiza la lista con los comunicados visibles
        comunicados = visibles

    return render(
        request,
        "comunicados/alumno.html",
        {
            "comunicados": comunicados
        }
    )

# VER PDF

# Permite abrir un PDF adjunto de un comunicado
def ver_pdf(request, id):

    try:

        # Busca el comunicado por su identificador
        comunicado = Comunicado.objects.get(
            id=id
        )

        # Comprueba que tenga un archivo PDF
        if not comunicado.archivo_pdf:

            raise Http404(
                "Este comunicado no tiene PDF adjunto."
            )

        # Devuelve el archivo PDF para visualizarlo
        return FileResponse(
            comunicado.archivo_pdf.open("rb"),
            content_type="application/pdf"
        )

    # Si no existe el comunicado muestra error 404
    except Comunicado.DoesNotExist:

        raise Http404(
            "Comunicado no encontrado."
        )

# MARCAR COMO LEÍDO

# Registra que un usuario leyó un comunicado
def marcar_leido(request, id):

    # Busca el comunicado seleccionado
    comunicado = get_object_or_404(
        Comunicado,
        id=id
    )

    # Crea el registro de lectura si no existe
    LecturaComunicado.objects.get_or_create(
        comunicado=comunicado,
        usuario=request.user
    )

    # Regresa al panel alumno
    return redirect(
        "comunicados:alumno"
    )

# ARCHIVAR PARA UN ALUMNO

# Archiva un comunicado solamente para un usuario específico
def archivar(request, id):

    # Busca el comunicado seleccionado
    comunicado = get_object_or_404(
        Comunicado,
        id=id
    )

    # Obtiene o crea el estado personal del alumno
    estado, creado = EstadoComunicado.objects.get_or_create(
        usuario=request.user,
        comunicado=comunicado
    )

    # Marca el comunicado como archivado para ese usuario
    estado.archivado = True

    estado.save()

    return redirect(
        "comunicados:alumno"
    )

# OCULTAR / ELIMINAR PARA UN ALUMNO

# Oculta un comunicado solamente para el usuario actual
def ocultar(request, id):

    # Busca el comunicado seleccionado
    comunicado = get_object_or_404(
        Comunicado,
        id=id
    )

    # Busca o crea el estado personal del usuario
    estado, creado = EstadoComunicado.objects.get_or_create(
        usuario=request.user,
        comunicado=comunicado
    )

    # Marca el comunicado como eliminado para ese usuario
    estado.eliminado = True

    estado.save()

    return redirect(
        "comunicados:alumno"
    )

# ELIMINAR DEFINITIVAMENTE

# Elimina el comunicado de la base de datos para todos los usuarios
def eliminar(request, id):

    # Busca el comunicado seleccionado
    comunicado = get_object_or_404(
        Comunicado,
        id=id
    )

    # Elimina permanentemente el comunicado
    comunicado.delete()

    # Regresa al panel directivo
    return redirect(
        "comunicados:directivo"
    )