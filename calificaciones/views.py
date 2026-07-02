from django.shortcuts import render, redirect
import unicodedata
from .models import AlumnoCalificacion


def _cargar_alumnos():
    return list(AlumnoCalificacion.objects.all().values())


def _guardar_alumnos(lista):
    for alumno in lista:
        obj, _ = AlumnoCalificacion.objects.update_or_create(
            id=alumno['id'],
            defaults={
                'nombre': alumno['nombre'],
                'curso': alumno['curso'],
                'division': alumno['division'],
                'materia': alumno['materia'],
                'nota1': alumno['nota1'],
                'nota2': alumno['nota2'],
            }
        )


_alumnos_cache = None


def _get_alumnos():
    global _alumnos_cache
    if _alumnos_cache is None:
        _alumnos_cache = _cargar_alumnos()
    return _alumnos_cache


mensajes_profesor = [
    # Lista fija de mensajes/avisos que el profesor dejó por materia.
    # A diferencia de "alumnos", esta lista NO se persiste en archivo:
    # vive solo en memoria y se reinicia cada vez que reiniciás el servidor.
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
    # Convierte un texto a una forma "canónica" para poder comparar
    # nombres/materias sin que importen mayúsculas, tildes o espacios extra.
    texto = texto.strip().lower()
    # strip(): quita espacios en blanco al principio y al final.
    # lower(): pasa todo el texto a minúsculas.

    texto = unicodedata.normalize("NFD", texto)
    # NFD (Normalization Form Decomposed) separa cada letra acentuada
    # en su letra base + el signo de acento como caracteres independientes.
    # Ejemplo: "é" se descompone en "e" + "´" (un carácter combinante aparte).

    texto = "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")
    # Recorre cada carácter del texto descompuesto y se queda solo con
    # los que NO sean de categoría Unicode "Mn" (Mark, nonspacing),
    # que es justamente la categoría de los acentos/diacríticos sueltos.
    # Resultado: el acento se elimina y queda solo la letra base.

    texto = " ".join(texto.split())
    # texto.split() divide el texto en palabras usando cualquier espacio
    # en blanco como separador (y descarta espacios extra).
    # " ".join(...) las vuelve a unir con un único espacio entre cada una.
    # Esto colapsa espacios múltiples en uno solo.

    return texto
    # Ejemplo completo: "  Lucía   Gómez " -> "lucia gomez"


def obtener_nombre_correcto(nombre_ingresado):
    # Dado un nombre tipeado por el usuario, busca si ya existe un alumno
    # con ese mismo nombre (ignorando tildes/mayúsculas/espacios) y, de
    # ser así, devuelve el nombre EXACTO como está guardado en la base,
    # para evitar duplicados con distinta ortografía.
    nombre_normalizado = normalizar_texto(nombre_ingresado)
    # Normalizamos el nombre ingresado para poder compararlo.

    for alumno in _get_alumnos():
        # Recorremos todos los alumnos ya cargados.
        if normalizar_texto(alumno["nombre"]) == nombre_normalizado:
            # Si el nombre normalizado de este alumno coincide con el
            # nombre normalizado ingresado...
            return alumno["nombre"]
            # ...devolvemos el nombre tal cual está guardado (con su
            # formato y tildes originales), no el que tipeó el usuario.

    return nombre_ingresado.strip().title()
    # Si no se encontró ningún alumno con ese nombre, es un alumno nuevo:
    # devolvemos el nombre ingresado, sin espacios sobrantes y con
    # la primera letra de cada palabra en mayúscula (.title()).


def obtener_nombres_alumnos():
    # Devuelve la lista de nombres de alumnos SIN repetidos (un alumno
    # puede aparecer varias veces en "alumnos" por tener varias materias).
    nombres = []
    # Lista final de nombres únicos, en su formato original (con tildes).
    nombres_normalizados = []
    # Lista paralela de nombres normalizados, para detectar duplicados
    # aunque estén escritos distinto (con/sin tilde, mayúsculas, etc).

    for alumno in _get_alumnos():
        nombre_normalizado = normalizar_texto(alumno["nombre"])
        # Normalizamos el nombre del alumno actual para compararlo.

        if nombre_normalizado not in nombres_normalizados:
            # Si todavía no agregamos un nombre equivalente a este...
            nombres.append(alumno["nombre"])
            # ...lo agregamos a la lista de nombres (con formato original).
            nombres_normalizados.append(nombre_normalizado)
            # ...y registramos su versión normalizada para no repetirlo.

    return nombres
    # Devuelve la lista de nombres únicos de alumnos.


def preparar_alumnos(lista):
    # Toma una lista de alumnos (diccionarios) y devuelve una nueva lista
    # con dos campos calculados agregados: "promedio" y "estado".
    resultado = []

    for alumno in lista:
        promedio = (alumno["nota1"] + alumno["nota2"]) / 2
        # Promedio simple entre las dos notas.

        if promedio >= 6:
            estado = "Aprobado"
        else:
            estado = "Desaprobado"
        # Regla de aprobación: 6 o más es "Aprobado".

        nuevo = alumno.copy()
        # Copiamos el diccionario del alumno para no modificar el original
        # (evita efectos secundarios sobre la lista "alumnos" global).
        nuevo["promedio"] = promedio
        nuevo["estado"] = estado
        resultado.append(nuevo)
        # Agregamos el alumno (con los campos extra) a la lista de resultado.

    return resultado


def obtener_materias():
    # Devuelve la lista de materias distintas que existen entre los alumnos.
    materias = []

    for alumno in _get_alumnos():
        if alumno["materia"] not in materias:
            # Si la materia de este alumno todavía no está en la lista...
            materias.append(alumno["materia"])
            # ...la agregamos (así evitamos materias repetidas).

    return materias


def existe_alumno_en_materia(nombre, materia, alumno_id_actual=None):
    # Verifica si ya existe un registro con el mismo alumno (nombre) y la
    # misma materia. Se usa para evitar cargar dos veces al mismo alumno
    # en la misma materia.
    # alumno_id_actual: si estamos EDITANDO un alumno, se pasa su propio id
    # para no compararlo consigo mismo (si no, siempre "se encontraría a sí mismo").
    nombre = normalizar_texto(nombre)
    materia = normalizar_texto(materia)
    # Normalizamos nombre y materia para comparar sin importar tildes/mayúsculas.

    for alumno in _get_alumnos():
        mismo_nombre = normalizar_texto(alumno["nombre"]) == nombre
        # ¿El nombre de este alumno coincide (normalizado) con el buscado?

        misma_materia = normalizar_texto(alumno["materia"]) == materia
        # ¿La materia de este alumno coincide (normalizada) con la buscada?

        distinto_id = alumno_id_actual is None or alumno["id"] != alumno_id_actual
        # Es True si:
        #  - no se pasó un id actual (estamos AGREGANDO, no editando), o
        #  - el id de este alumno es distinto al que estamos editando
        #    (para no comparar el registro consigo mismo).

        if mismo_nombre and misma_materia and distinto_id:
            # Si coincide nombre, materia, y no es el mismo registro que
            # estamos editando, entonces SÍ hay un duplicado.
            return True

    return False
    # Si terminamos de recorrer todo sin encontrar duplicado, no existe.


def inicio(request):
    # Vista de la página de inicio. Simplemente renderiza el template,
    # sin pasarle datos adicionales.
    return render(request, "calificaciones/index.html")


def profesor(request):
    # Vista del panel del profesor: muestra los alumnos de una materia
    # seleccionada, junto con el listado de materias disponibles.
    materia = request.GET.get("materia")
    # Lee el parámetro "materia" de la URL (ej: ?materia=Matemática).
    # Si no viene, "materia" queda en None.

    materias = obtener_materias()
    # Lista de todas las materias existentes (para armar un selector/filtro).

    lista = preparar_alumnos(_get_alumnos())
    # Alumnos con "promedio" y "estado" ya calculados.

    if materia:
        # Si se seleccionó una materia específica...
        lista = [alumno for alumno in lista if alumno["materia"] == materia]
        # ...filtramos la lista para mostrar solo los alumnos de esa materia.
    else:
        # Si no se seleccionó ninguna materia...
        lista = []
        # ...no mostramos ningún alumno (se espera que el profesor elija
        # una materia primero).

    return render(request, "calificaciones/profesor.html", {
        "alumnos": lista,
        "materias": materias,
        "materia_seleccionada": materia,
    })
    # Renderiza el template pasándole: los alumnos a mostrar, las materias
    # disponibles, y cuál materia está actualmente seleccionada
    # (para por ejemplo resaltarla en el HTML).


def agregar_alumno(request):
    # Vista para agregar un nuevo registro de alumno (alumno + materia + notas).
    error = ""
    # Mensaje de error a mostrar en el formulario (vacío si no hay error).

    nombres_alumnos = obtener_nombres_alumnos()
    # Lista de nombres existentes, posiblemente usada para autocompletar
    # en el formulario HTML.

    if request.method == "POST":
        # Si el formulario fue enviado (envío de datos)...
        nombre = request.POST.get("nombre")
        curso = request.POST.get("curso")
        division = request.POST.get("division")
        materia = request.POST.get("materia")
        nota1 = request.POST.get("nota1")
        nota2 = request.POST.get("nota2")
        # Leemos cada campo enviado desde el formulario HTML.

        nombre_correcto = obtener_nombre_correcto(nombre)
        # Si el nombre ya existía (con otra ortografía/tildes), usamos
        # la versión ya guardada, para mantener consistencia.

        if existe_alumno_en_materia(nombre_correcto, materia):
            # Si ya existe un registro de ese alumno en esa materia...
            error = "Ese alumno ya está cargado en esa materia. Puede estar en otras materias, pero no repetido en la misma."
            # ...no lo agregamos, y mostramos un mensaje de error.
        else:
            _alumnos = _get_alumnos()
            nuevo_id = max((a["id"] for a in _alumnos), default=0) + 1  # ← ID seguro
            # Calculamos un nuevo id único: el máximo id actual + 1.
            # default=0 evita un error si la lista "alumnos" estuviera vacía
            # (en ese caso, el primer id sería 1).

            _alumnos.append({
                "id": nuevo_id,
                "nombre": nombre_correcto,
                "curso": curso,
                "division": division,
                "materia": materia,
                "nota1": int(nota1),
                "nota2": int(nota2),
                # Convertimos las notas a int, ya que request.POST las
                # entrega siempre como texto (string).
            })
            _guardar_alumnos(_get_alumnos())  # ← guarda en disco
            # Persistimos los cambios en el archivo JSON, para que no se
            # pierdan si se reinicia el servidor.

            return redirect(f"/calificaciones/profesor/?materia={materia}")
            # Tras guardar, redirigimos al panel del profesor, ya filtrado
            # por la materia recién cargada (esto también evita el
            # reenvío del formulario si el usuario refresca la página).

    return render(request, "calificaciones/formulario_alumno.html", {
        "titulo": "Agregar alumno",
        "boton": "Guardar alumno",
        "error": error,
        "alumno": None,
        # "alumno": None indica que el formulario está vacío (modo "alta",
        # no estamos editando uno existente).
        "nombres_alumnos": nombres_alumnos,
    })
    # Si la petición fue GET (o si hubo error en el POST), se vuelve a
    # mostrar el formulario, con el error si lo hubiera.


def editar_alumno(request, alumno_id):
    # Vista para editar/calificar un alumno ya existente, identificado
    # por su "alumno_id" (viene como parte de la URL, ej: /editar/3/).
    alumno_encontrado = None

    for alumno in _get_alumnos():
        if alumno["id"] == alumno_id:
            alumno_encontrado = alumno
            # Guardamos una REFERENCIA al diccionario (no una copia),
            # así que modificarlo más abajo modifica directamente la
            # lista global "alumnos".

    if alumno_encontrado is None:
        # Si no se encontró ningún alumno con ese id (id inválido)...
        return redirect("/calificaciones/profesor/")
        # ...redirigimos al panel del profesor para evitar un error.

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
            # Comprobamos duplicado, mandando alumno_id para que el propio
            # registro que se está editando no cuente como "duplicado".
            error = "Ese alumno ya está cargado en esa materia. No se puede duplicar."
        else:
            alumno_encontrado["nombre"] = nombre_correcto
            alumno_encontrado["curso"] = curso
            alumno_encontrado["division"] = division
            alumno_encontrado["materia"] = materia
            alumno_encontrado["nota1"] = int(nota1)
            alumno_encontrado["nota2"] = int(nota2)
            # Como "alumno_encontrado" es una referencia al diccionario
            # dentro de la lista "alumnos", estas asignaciones actualizan
            # directamente ese registro en la lista global.

            _guardar_alumnos(_get_alumnos())  # ← guarda en disco
            # Persistimos los cambios en el archivo JSON.

            return redirect(f"/calificaciones/profesor/?materia={materia}")
            # Redirigimos al panel del profesor filtrado por la materia.

    return render(request, "calificaciones/formulario_alumno.html", {
        "titulo": "Editar / Calificar alumno",
        "boton": "Guardar cambios",
        "error": error,
        "alumno": alumno_encontrado,
        # Acá "alumno" SÍ tiene datos, para que el formulario se muestre
        # precargado con la info actual del alumno (modo "edición").
        "nombres_alumnos": nombres_alumnos,
    })


def alumno(request):
    # Vista que muestra las calificaciones desde la perspectiva del alumno
    # (probablemente de solo lectura, sin opción de editar).
    materia = request.GET.get("materia")
    # Lee el filtro de materia desde la URL, si lo hay.

    lista = preparar_alumnos(_get_alumnos())
    # Todos los alumnos con promedio y estado ya calculados.

    materias = obtener_materias()
    # Lista de materias para el filtro/selector.

    if materia:
        lista = [alumno for alumno in lista if alumno["materia"] == materia]
        # Si se seleccionó una materia, filtramos la lista.
        # Nota: a diferencia de la vista "profesor", acá si NO se elige
        # materia, se muestran TODOS los alumnos (no se vacía la lista).

    return render(request, "calificaciones/alumno.html", {
        "alumnos": lista,
        "materias": materias,
        "materia_seleccionada": materia,
    })


def mensajes(request):
    # Vista simple que muestra los mensajes/avisos del profesor por materia.
    return render(request, "calificaciones/mensajes.html", {
        "mensajes": mensajes_profesor,
    })
def boletin(request):
    return render(request, "calificaciones/boletin.html")