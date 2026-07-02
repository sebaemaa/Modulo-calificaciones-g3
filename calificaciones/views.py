from django.shortcuts import render, redirect
import unicodedata
from .models import AlumnoCalificacion


mensajes_profesor = [
    # Lista fija de mensajes/avisos que el profesor dejó por materia.
    # Sigue viviendo solo en memoria (se reinicia con el servidor),
    # tal cual estaba en el original.
    {
        "materia": "Matemática",
        "titulo": "Revisión de evaluación",
        "contenido": "Recordá revisar los ejercicios corregidos antes de la próxima clase.",
    },
    {
        "materia": "Lengua",
        "titulo": "Trabajo práctico",
        "contenido": "La entrega del trabajo práctico será tenida en cuenta para la nota final.",
    },
    {
        "materia": "Historia",
        "titulo": "Participación en clase",
        "contenido": "Se recomienda reforzar la participación y repasar los temas vistos.",
    },
]


def normalizar_texto(texto):
    # Convierte un texto a una forma "canónica" para comparar nombres/materias
    # sin que importen mayúsculas, tildes o espacios extra.
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")
    texto = " ".join(texto.split())
    return texto


def preparar_alumnos(queryset):
    # Recibe un queryset (no una lista global) y devuelve una lista de
    # diccionarios con "promedio" y "estado" ya calculados.
    resultado = []
    for alumno in queryset:
        promedio = (alumno.nota1 + alumno.nota2) / 2
        estado = "Aprobado" if promedio >= 6 else "Desaprobado"
        resultado.append({
            "id": alumno.id,
            "nombre": alumno.nombre,
            "curso": alumno.curso,
            "division": alumno.division,
            "materia": alumno.materia,
            "nota1": alumno.nota1,
            "nota2": alumno.nota2,
            "promedio": promedio,
            "estado": estado,
        })
    return resultado
    # Nota: esto se podría simplificar todavía más agregando "promedio" y
    # "estado" como @property en el modelo AlumnoCalificacion. Te lo dejo
    # como sugerencia por si querés dar ese paso después.


def obtener_materias():
    # Antes recorría la lista global a mano. El ORM ya hace el distinct.
    return list(
        AlumnoCalificacion.objects
        .order_by("materia")
        .values_list("materia", flat=True)
        .distinct()
    )


def obtener_nombre_correcto(nombre_ingresado):
    # Busca si ya existe un alumno con ese nombre (ignorando tildes/mayúsculas)
    # consultando la base directamente, no una copia vieja en memoria.
    nombre_normalizado = normalizar_texto(nombre_ingresado)

    for nombre_existente in AlumnoCalificacion.objects.values_list("nombre", flat=True).distinct():
        if normalizar_texto(nombre_existente) == nombre_normalizado:
            return nombre_existente

    return nombre_ingresado.strip().title()


def obtener_nombres_alumnos():
    # Nombres únicos de alumnos, consultando la base cada vez.
    nombres = []
    normalizados = []

    for nombre in AlumnoCalificacion.objects.values_list("nombre", flat=True).distinct():
        norm = normalizar_texto(nombre)
        if norm not in normalizados:
            nombres.append(nombre)
            normalizados.append(norm)

    return nombres


def existe_alumno_en_materia(nombre, materia, alumno_id_actual=None):
    # Sigue comparando en Python (por la normalización de tildes),
    # pero sobre un queryset fresco en vez de la lista global vieja.
    nombre_normalizado = normalizar_texto(nombre)
    materia_normalizada = normalizar_texto(materia)

    queryset = AlumnoCalificacion.objects.all()
    if alumno_id_actual is not None:
        queryset = queryset.exclude(id=alumno_id_actual)

    for alumno in queryset:
        if (normalizar_texto(alumno.nombre) == nombre_normalizado
                and normalizar_texto(alumno.materia) == materia_normalizada):
            return True

    return False


def inicio(request):
    return render(request, "calificaciones/index.html")


def profesor(request):
    materia = request.GET.get("materia")
    materias = obtener_materias()

    if materia:
        lista = preparar_alumnos(AlumnoCalificacion.objects.filter(materia=materia))
    else:
        lista = []

    return render(request, "calificaciones/profesor.html", {
        "alumnos": lista,
        "materias": materias,
        "materia_seleccionada": materia,
    })


def agregar_alumno(request):
    error = ""
    nombres_alumnos = obtener_nombres_alumnos()

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        curso = request.POST.get("curso")
        division = request.POST.get("division")
        materia = request.POST.get("materia")
        nota1 = request.POST.get("nota1")
        nota2 = request.POST.get("nota2")

        nombre_correcto = obtener_nombre_correcto(nombre)

        if existe_alumno_en_materia(nombre_correcto, materia):
            error = "Ese alumno ya está cargado en esa materia. Puede estar en otras materias, pero no repetido en la misma."
        else:
            # El ORM genera el id solo. Nada de max(id)+1 a mano.
            AlumnoCalificacion.objects.create(
                nombre=nombre_correcto,
                curso=curso,
                division=division,
                materia=materia,
                nota1=int(nota1),
                nota2=int(nota2),
            )
            return redirect(f"/calificaciones/profesor/?materia={materia}")

    return render(request, "calificaciones/formulario_alumno.html", {
        "titulo": "Agregar alumno",
        "boton": "Guardar alumno",
        "error": error,
        "alumno": None,
        "nombres_alumnos": nombres_alumnos,
    })


def editar_alumno(request, alumno_id):
    # Un solo SELECT por id, en vez de recorrer la lista global a mano.
    alumno_encontrado = AlumnoCalificacion.objects.filter(id=alumno_id).first()

    if alumno_encontrado is None:
        return redirect("/calificaciones/profesor/")

    error = ""
    nombres_alumnos = obtener_nombres_alumnos()

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        curso = request.POST.get("curso")
        division = request.POST.get("division")
        materia = request.POST.get("materia")
        nota1 = request.POST.get("nota1")
        nota2 = request.POST.get("nota2")

        nombre_correcto = obtener_nombre_correcto(nombre)

        if existe_alumno_en_materia(nombre_correcto, materia, alumno_id_actual=alumno_id):
            error = "Ese alumno ya está cargado en esa materia. No se puede duplicar."
        else:
            alumno_encontrado.nombre = nombre_correcto
            alumno_encontrado.curso = curso
            alumno_encontrado.division = division
            alumno_encontrado.materia = materia
            alumno_encontrado.nota1 = int(nota1)
            alumno_encontrado.nota2 = int(nota2)
            alumno_encontrado.save()

            return redirect(f"/calificaciones/profesor/?materia={materia}")

    return render(request, "calificaciones/formulario_alumno.html", {
        "titulo": "Editar / Calificar alumno",
        "boton": "Guardar cambios",
        "error": error,
        "alumno": alumno_encontrado,
        "nombres_alumnos": nombres_alumnos,
    })


def alumno(request):
    materia = request.GET.get("materia")
    materias = obtener_materias()

    queryset = AlumnoCalificacion.objects.all()
    if materia:
        queryset = queryset.filter(materia=materia)

    lista = preparar_alumnos(queryset)

    return render(request, "calificaciones/alumno.html", {
        "alumnos": lista,
        "materias": materias,
        "materia_seleccionada": materia,
    })


def mensajes(request):
    return render(request, "calificaciones/mensajes.html", {
        "mensajes": mensajes_profesor,
    })


def boletin(request):
    return render(request, "calificaciones/boletin.html")