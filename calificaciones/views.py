from django.shortcuts import render, redirect
import unicodedata
from .models import AlumnoCalificacion


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
    # Quita tildes, espacios extra y pasa a minúsculas para poder comparar
    # nombres/materias sin importar cómo los escribió el usuario.
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " ".join(texto.split())


def armar_lista(queryset):
    # Convierte el queryset en una lista de diccionarios con promedio y estado
    # ya calculados, lista para pasar al template.
    lista=[]
    for a in queryset:
        promedio = (a.nota1 + a.nota2) / 2
        lista.append({
            "id": a.id,
            "nombre": a.nombre,
            "curso": a.curso,
            "division": a.division,
            "materia": a.materia,
            "nota1": a.nota1,
            "nota2": a.nota2,
            "promedio": promedio,
            "estado": "Aprobado" if promedio >= 6 else "Desaprobado",
        })
    return lista


def inicio(request):
    return render(request, "calificaciones/index.html")


def profesor(request):
    materia = request.GET.get("materia")
    materias = list(
        AlumnoCalificacion.objects.order_by("materia")
        .values_list("materia", flat=True).distinct()
    )

    lista = armar_lista(AlumnoCalificacion.objects.filter(materia=materia)) if materia else []

    return render(request, "calificaciones/profesor.html", {
        "alumnos": lista,
        "materias": materias,
        "materia_seleccionada": materia,
    })


def agregar_alumno(request):
    error = ""
    nombres_alumnos = list(AlumnoCalificacion.objects.values_list("nombre", flat=True).distinct())

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip().title()
        curso = request.POST.get("curso")
        division = request.POST.get("division")
        materia = request.POST.get("materia")
        nota1 = request.POST.get("nota1")
        nota2 = request.POST.get("nota2")

        # Reutiliza el nombre ya guardado si existe uno equivalente (sin tildes/mayúsculas)
        nombre_norm = normalizar_texto(nombre)
        for existente in AlumnoCalificacion.objects.values_list("nombre", flat=True).distinct():
            if normalizar_texto(existente) == nombre_norm:
                nombre = existente
                break

        ya_existe = AlumnoCalificacion.objects.filter(
            nombre=nombre, materia=materia
        ).exists()

        if ya_existe:
            error = "Ese alumno ya está cargado en esa materia."
        else:
            AlumnoCalificacion.objects.create(
                nombre=nombre, curso=curso, division=division,
                materia=materia, nota1=int(nota1), nota2=int(nota2),
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
    alumno_encontrado = AlumnoCalificacion.objects.filter(id=alumno_id).first()
    if alumno_encontrado is None:
        return redirect("/calificaciones/profesor/")

    error = ""
    nombres_alumnos = list(AlumnoCalificacion.objects.values_list("nombre", flat=True).distinct())

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip().title()
        curso = request.POST.get("curso")
        division = request.POST.get("division")
        materia = request.POST.get("materia")
        nota1 = request.POST.get("nota1")
        nota2 = request.POST.get("nota2")

        nombre_norm = normalizar_texto(nombre)
        for existente in AlumnoCalificacion.objects.values_list("nombre", flat=True).distinct():
            if normalizar_texto(existente) == nombre_norm:
                nombre = existente
                break

        ya_existe = AlumnoCalificacion.objects.filter(
            nombre=nombre, materia=materia
        ).exclude(id=alumno_id).exists()

        if ya_existe:
            error = "Ese alumno ya está cargado en esa materia."
        else:
            alumno_encontrado.nombre = nombre
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
    materias = list(
        AlumnoCalificacion.objects.order_by("materia")
        .values_list("materia", flat=True).distinct()
    )

    queryset = AlumnoCalificacion.objects.all()
    if materia:
        queryset = queryset.filter(materia=materia)

    return render(request, "calificaciones/alumno.html", {
        "alumnos": armar_lista(queryset),
        "materias": materias,
        "materia_seleccionada": materia,
    })

def mensajes(request):
    return render(request, "calificaciones/mensajes.html", {
        "mensajes": mensajes_profesor,
    })