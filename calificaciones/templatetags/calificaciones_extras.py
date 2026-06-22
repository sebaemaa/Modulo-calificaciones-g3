from django import template  # Importa el módulo de template tags de Django

register = template.Library()  # Crea una instancia de Library para registrar filtros y tags personalizados


@register.filter  # Decorador: registra esta función como un filtro usable en templates Django
def dictget(d, key):
    """Accede a un diccionario con clave variable en templates Django.
    Uso en plantilla: {{ mi_dict|dictget:variable_clave }}
    Los templates de Django no permiten corchetes (dict[key]) directamente,
    así que este filtro reemplaza esa sintaxis.
    """
    if d is None:  # Si el diccionario es None, devuelve None sin tirar error
        return None
    return d.get(key)  # Llama a dict.get(key): devuelve el valor o None si la clave no existe
