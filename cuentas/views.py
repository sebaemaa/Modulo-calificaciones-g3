from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

DESTINO_POR_ROL = {
    'administrativo': '/alumnos/',
    'directivo': '/docentes/',
    'docente': '/asistencia/',
    'alumno': '/calificaciones/',
}


@login_required
def despues_del_login(request):
    """Manda a cada usuario a su seccion segun el rol."""
    perfil = getattr(request.user, 'perfil', None)
    destino = DESTINO_POR_ROL.get(perfil.rol, '/') if perfil else '/'
    return redirect(destino)
