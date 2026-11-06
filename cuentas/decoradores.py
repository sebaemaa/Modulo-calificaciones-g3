from functools import wraps
from urllib.parse import quote

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def rol_requerido(*roles):
    """Permite el acceso solo a usuarios cuyo perfil tenga alguno de los roles dados.

    Uso:
        @rol_requerido('docente', 'administrativo')
        def cargar_notas(request):
            ...
    """
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                destino = quote(request.get_full_path(), safe='/')
                return redirect(f"{reverse('login')}?next={destino}")

            if request.user.is_superuser:
                return vista(request, *args, **kwargs)

            perfil = getattr(request.user, 'perfil', None)
            if perfil is None:
                messages.error(request, "Tu usuario todavia no tiene un perfil asignado.")
                return redirect('/')

            if perfil.rol not in roles:
                messages.error(request, "No tenes permiso para acceder a esta seccion.")
                return redirect('/')

            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
