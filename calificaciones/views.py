from django.shortcuts import render, redirect
import unicodedata


alumnos = [
    {
        "id": 1,
        "nombre": "Juan Pérez",
        "curso": "1°",
        "division": "A",
        "materia": "Matemática",
        "nota1": 8,
        "nota2": 7,
    },
    {
        "id": 2,
        "nombre": "Juan Pérez",
        "curso": "1°",
        "division": "A",
        "materia": "Lengua",
        "nota1": 7,
        "nota2": 8,
    },
    {
        "id": 3,
        "nombre": "Lucía Gómez",
        "curso": "2°",
        "division": "B",
        "materia": "Matemática",
        "nota1": 9,
        "nota2": 8,
    },
    {
        "id": 4,
        "nombre": "Mateo Ruiz",
        "curso": "3°",
        "division": "A",
        "materia": "Historia",
        "nota1": 5,
        "nota2": 6,
    },
]


mensajes_profesor = [
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
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")
    texto = " ".join(texto.split())
    return texto


def obtener_nombre_correcto(nombre_ingresado):
    nombre_normalizado = normalizar_texto(nombre_ingresado)

    for alumno in alumnos:
        if normalizar_texto(alumno["nombre"]) == nombre_normalizado:
            return alumno["nombre"]

    return nombre_ingresado.strip().title()


def obtener_nombres_alumnos():
    nombres = []
    nombres_normalizados = []

    for alumno in alumnos:
        nombre_normalizado = normalizar_texto(alumno["nombre"])

        if nombre_normalizado not in nombres_normalizados:
            nombres.append(alumno["nombre"])
            nombres_normalizados.append(nombre_normalizado)

    return nombres


def preparar_alumnos(lista):
    resultado = []

    for alumno in lista:
        promedio = (alumno["nota1"] + alumno["nota2"]) / 2

        if promedio >= 6:
            estado = "Aprobado"
        else:
            estado = "Desaprobado"

        nuevo = alumno.copy()
        nuevo["promedio"] = promedio
        nuevo["estado"] = estado
        resultado.append(nuevo)

    return resultado


def obtener_materias():
    materias = []

    for alumno in alumnos:
        if alumno["materia"] not in materias:
            materias.append(alumno["materia"])

    return materias


def existe_alumno_en_materia(nombre, materia, alumno_id_actual=None):
    nombre = normalizar_texto(nombre)
    materia = normalizar_texto(materia)

    for alumno in alumnos:
        mismo_nombre = normalizar_texto(alumno["nombre"]) == nombre
        misma_materia = normalizar_texto(alumno["materia"]) == materia
        distinto_id = alumno_id_actual is None or alumno["id"] != alumno_id_actual

        if mismo_nombre and misma_materia and distinto_id:
            return True

    return False


def inicio(request):
    return render(request, "calificaciones/index.html")


def profesor(request):
    materia = request.GET.get("materia")
    materias = obtener_materias()
    lista = preparar_alumnos(alumnos)

    if materia:
        lista = [alumno for alumno in lista if alumno["materia"] == materia]
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
            nuevo_id = len(alumnos) + 1

            alumnos.append({
                "id": nuevo_id,
                "nombre": nombre_correcto,
                "curso": curso,
                "division": division,
                "materia": materia,
                "nota1": int(nota1),
                "nota2": int(nota2),
            })

            return redirect(f"/calificaciones/profesor/?materia={materia}")

    return render(request, "calificaciones/formulario_alumno.html", {
        "titulo": "Agregar alumno",
        "boton": "Guardar alumno",
        "error": error,
        "alumno": None,
        "nombres_alumnos": nombres_alumnos,
    })


def editar_alumno(request, alumno_id):
    alumno_encontrado = None

    for alumno in alumnos:
        if alumno["id"] == alumno_id:
            alumno_encontrado = alumno

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
            alumno_encontrado["nombre"] = nombre_correcto
            alumno_encontrado["curso"] = curso
            alumno_encontrado["division"] = division
            alumno_encontrado["materia"] = materia
            alumno_encontrado["nota1"] = int(nota1)
            alumno_encontrado["nota2"] = int(nota2)

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
    lista = preparar_alumnos(alumnos)
    materias = obtener_materias()

    if materia:
        lista = [alumno for alumno in lista if alumno["materia"] == materia]

    return render(request, "calificaciones/alumno.html", {
        "alumnos": lista,
        "materias": materias,
        "materia_seleccionada": materia,
    })


def mensajes(request):
    return render(request, "calificaciones/mensajes.html", {
        "mensajes": mensajes_profesor,
    })