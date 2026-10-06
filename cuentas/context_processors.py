def perfil_usuario(request):
    """Deja el perfil disponible en todas las plantillas como {{ perfil }}."""
    if request.user.is_authenticated:
        return {'perfil': getattr(request.user, 'perfil', None)}
    return {'perfil': None}
