from django.shortcuts import render, redirect, get_object_or_404  # render(): combina una plantilla HTML con datos (contexto) y devuelve un HttpResponse; redirect(): devuelve una respuesta HTTP 302 que redirige el navegador a otra URL; get_object_or_404(): busca un objeto en BD o lanza HTTP 404 (page not found)
from django.contrib import messages  # messages: framework de Django para mostrar mensajes al usuario en la próxima página. Los mensajes se guardan en la sesión y se borran después de mostrarse (flash messages)
from django.http import HttpResponse  # HttpResponse: construye una respuesta HTTP manual. Se usa para enviar archivos (CSV) en vez de HTML
from decimal import Decimal, InvalidOperation  # Decimal: tipo numérico de Python con precisión exacta (evita errores de coma flotante como 0.1 + 0.2 != 0.3). InvalidOperation: excepción que se lanza cuando Decimal() recibe un string no numérico
import csv  # Módulo de la biblioteca estándar de Python para leer y escribir archivos CSV (valores separados por coma)
import unicodedata  # Módulo de la biblioteca estándar para trabajar con caracteres Unicode. Se usa para normalizar texto (quitar acentos)
from .models import Curso, Alumno, Evaluacion, Mensaje, NotaDireccion  # Importa TODOS los modelos definidos en models.py de la misma app


# ==============================================================================
# FUNCIONES AUXILIARES: se usan desde varias vistas
# ==============================================================================

def normalizar_texto(texto):  # Recibe un string, devuelve el string en minúsculas, sin acentos y sin espacios múltiples. Sirve para comparar nombres ignorando diferencias de mayúsculas, tildes y espacios
    texto = texto.strip().lower()  # strip(): elimina espacios al inicio y final. lower(): convierte todo a minúsculas para comparación case-insensitive
    texto = unicodedata.normalize("NFD", texto)  # normalize("NFD"): descompone caracteres acentuados en su forma base + diacrítico. Ej: "é" → "e" + combinación de acento (U+0301)
    texto = "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")  # Filtra caracteres cuya categoría Unicode NO sea "Mn" (Mark, Nonspacing). Mn = acentos, diéresis, etc. El resultado es "e" en vez de "é"
    texto = " ".join(texto.split())  # split() sin argumentos divide por cualquier espacio y elimina vacíos. join() con " " los vuelve a unir con un solo espacio. Normaliza espacios múltiples
    return texto


def obtener_nombre_correcto(nombre_ingresado):  # Busca en la BD si ya existe un alumno con ese nombre (normalizado). Si existe, devuelve el nombre guardado (con su capitalización original). Si no, aplica title() (primera letra de cada palabra en mayúscula)
    nombre_norm = normalizar_texto(nombre_ingresado)  # Normaliza el nombre que ingresó el usuario para poder compararlo
    for alumno in Alumno.objects.all():  # Itera sobre TODOS los alumnos de la BD (es ineficiente con muchos alumnos, pero funciona para este proyecto)
        if normalizar_texto(alumno.nombre) == nombre_norm:  # Compara versiones normalizadas. Si coinciden, significa que el alumno ya existe con otra capitalización (ej: "juan perez" vs "Juan Pérez")
            return alumno.nombre  # Devuelve el nombre EXACTO que está guardado en la BD (con mayúsculas, acentos, etc. originales)
    return nombre_ingresado.strip().title()  # Si no encontró coincidencia, aplica title(): convierte "juan" → "Juan". strip() por si hay espacios


def obtener_promedio(evaluaciones_queryset):  # Recibe un QuerySet de Evaluacion, calcula el promedio de los valores numéricos ignorando los None (sin nota)
    valores = [float(e.valor) for e in evaluaciones_queryset if e.valor is not None]  # List comprehension: itera cada evaluación, filtra las que tienen valor not None, y extrae valor como float
    if not valores:  # Si la lista está vacía (ninguna evaluación tiene nota)
        return 0  # Devuelve 0 para evitar división por cero
    return round(sum(valores) / len(valores), 2)  # Suma todos los valores, divide por cantidad (promedio), redondea a 2 decimales


def obtener_estado(promedio, alumno=None):  # Determina TEA (aprobado), TEP (en proceso) o TED (desaprobado). Si el alumno tiene estado manual, usa ese; sino calcula según el promedio
    if alumno and alumno.estado:  # Si se pasó un objeto Alumno y tiene un estado manual guardado (string no vacío)
        return alumno.estado  # Devuelve el estado que el profesor setteó manualmente (sobrescribe el cálculo automático)
    if promedio >= 7:  # Promedio mayor o igual a 7
        return "TEA"  # TEA = Trabajo en Equipo Aprobado
    if promedio >= 4:  # Promedio entre 4 y 6.99
        return "TEP"  # TEP = Trabajo en Equipo en Proceso (equivalente a "cursando" o "regular")
    return "TED"  # Promedio menor a 4: TED = Trabajo en Equipo Desaprobado


def parsear_nota(texto):  # Convierte un string de texto a Decimal de forma segura. Reemplaza comas por puntos (formato argentino: "8,5" → "8.5"). Devuelve None si el texto está vacío o no es un número válido
    texto = texto.strip().replace(",", ".")  # strip() elimina espacios; replace() normaliza el separador decimal argentino para que Decimal() lo entienda
    if not texto:  # Si el string quedó vacío después de limpiar (el usuario no escribió nada)
        return None  # Devuelve None: significa "sin nota", no "nota 0"
    try:
        return Decimal(texto)  # Intenta convertir el texto a tipo Decimal (precisión exacta, no float). Decimal("8.5") → 8.5
    except InvalidOperation:  # Si Decimal() falla porque el texto no es un número reconocible
        return None  # Devuelve None


# ==============================================================================
# VISTAS DEL MÓDULO
# ==============================================================================

def inicio(request):  # Vista del homepage de calificaciones. request es un objeto HttpRequest que Django crea automáticamente con los datos de la petición del navegador
    return render(request, "calificaciones/index.html")  # render() busca la plantilla index.html dentro de templates/calificaciones/, la procesa y devuelve un HttpResponse con el HTML resultante


# ---------------------------------------------------------------------------
# PROFESOR: selector de cursos
# ---------------------------------------------------------------------------

def profesor(request):  # Vista que lista todos los cursos disponibles. No recibe parámetros extra, solo el request
    cursos = Curso.objects.all().order_by("-año", "curso", "division", "materia")  # Curso.objects.all(): SELECT * FROM calificaciones_curso. order_by(): ORDER BY año DESC, curso ASC, division ASC, materia ASC
    return render(request, "calificaciones/profesor.html", {"cursos": cursos})  # Pasa la variable "cursos" a la plantilla para que la muestre. El diccionario {"cursos": cursos} es el "contexto"


# ---------------------------------------------------------------------------
# PROFESOR: grilla editable del curso (tipo Excel)
# ---------------------------------------------------------------------------

def ver_curso(request, curso_id):  # Vista principal del profesor. Recibe curso_id desde la URL (capturado por <int:curso_id> en urls.py)
    curso = get_object_or_404(Curso, id=curso_id)  # get_object_or_404: intenta Curso.objects.get(id=curso_id). Si no existe o el id no es válido, lanza HTTP 404 automáticamente
    alumnos = Alumno.objects.filter(curso=curso).order_by("nombre")  # filter(): SELECT WHERE curso_id = curso.id. order_by(): ORDER BY nombre. Devuelve un QuerySet (lista perezosa)

    tipos = (  # Obtiene los nombres de los tipos de evaluación (las columnas dinámicas de la grilla)
        Evaluacion.objects.filter(alumno__curso=curso)  # alumno__curso: doble guión bajo significa "seguir la FK". Django traduce: Evaluacion JOIN Alumno WHERE Alumno.curso_id = curso.id
        .values_list("tipo", flat=True)  # values_list("tipo", flat=True): en vez de objetos Evaluacion, devuelve solo los valores del campo "tipo" como lista plana (no tuplas)
        .distinct()  # DISTINCT en SQL: elimina tipos repetidos. Un tipo puede aparecer en muchos alumnos, pero solo nos interesa una vez
        .order_by("tipo")  # ORDER BY tipo ASC
    )

    if request.method == "POST":  # request.method indica si el navegador envió GET (cargar página) o POST (enviar formulario). POST significa que el profesor hizo clic en "Guardar cambios"
        errores = []  # Lista para acumular mensajes de error de validación
        for key, value in request.POST.items():  # request.POST es un diccionario como QueryDict con todos los campos del formulario. items() devuelve pares (name_del_input, valor)
            if key.startswith("eval_"):  # Filtra inputs cuyo name empieza con "eval_". Los inputs de nota tienen name="eval_<id_alumno>_<tipo>"
                parts = key.split("_", 2)  # split("_", 2): divide el string en máximo 3 partes. "eval_5_TP 1" → ["eval", "5", "TP 1"]
                try:
                    alumno_id = int(parts[1])  # Convierte la segunda parte a entero: el ID del alumno
                    tipo_eval = parts[2]  # La tercera parte es el nombre del tipo de evaluación
                except (IndexError, ValueError):  # IndexError: si el formato no tiene 3 partes (no debería pasar). ValueError: si el ID no es número
                    continue  # Salta este campo y sigue con el siguiente
                nota = parsear_nota(value)  # Convierte el valor del input a Decimal (None si está vacío)
                if nota is not None and (nota < 1 or nota > 10):  # Si tiene valor pero está fuera del rango permitido
                    try:
                        nom = Alumno.objects.get(id=alumno_id).nombre  # Busca el nombre del alumno para mostrar en el mensaje de error
                    except Alumno.DoesNotExist:  # Si el alumno no existe (raro, pero por seguridad)
                        nom = f"ID {alumno_id}"  # Usa "ID X" como nombre genérico
                    errores.append(f"{nom} - {tipo_eval}: {nota} no es válida (debe ser entre 1 y 10)")  # Agrega el error a la lista
                    continue  # No guarda esta nota, pasa a la siguiente
                try:
                    Evaluacion.objects.update_or_create(  # update_or_create: busca una evaluación con (alumno_id, tipo). Si existe, actualiza su valor. Si no existe, la crea
                        alumno_id=alumno_id,  # Parámetros de búsqueda: alumno_id (clave foránea directa, evita cargar el objeto Alumno)
                        tipo=tipo_eval,  # Tipo de evaluación
                        defaults={"valor": nota},  # defaults: si encuentra, UPDATE valor = nota; si no encuentra, INSERT con estos valores además de los de búsqueda
                    )
                except Exception:  # Captura cualquier excepción genérica (error de BD, integridad, etc.)
                    continue  # Ignora el error y sigue con el próximo campo

        # Guardar el estado manual de cada alumno
        for key, value in request.POST.items():  # Segundo bucle: ahora procesa los campos de estado
            if key.startswith("estado_"):  # Los selects de estado tienen name="estado_<alumno_id>"
                alumno_id = key.split("_", 1)[1]  # split("_", 1): divide en ["estado", "alumno_id"] y toma la segunda parte
                try:
                    Alumno.objects.filter(id=alumno_id).update(  # filter().update(): actualiza directamente en BD sin cargar el objeto (más eficiente que .save())
                        estado=value.strip() or None  # Si value está vacío, guarda None en la BD (borra el estado manual)
                    )
                except Exception:
                    continue

        if errores:  # Si la lista de errores no está vacía
            messages.warning(request, "Algunas notas no se guardaron:")  # messages.warning: muestra un mensaje de advertencia (color amarillo) en la próxima página
            for e in errores:  # Agrega cada error como un mensaje separado
                messages.warning(request, e)
        else:  # Si no hubo errores
            messages.success(request, "Calificaciones guardadas correctamente.")  # messages.success: mensaje verde de éxito
        return redirect("ver_curso", curso_id=curso_id)  # redirect() con name de URL: Django busca la URL con name="ver_curso" y completa con curso_id. Esto evita reenviar el POST al recargar la página (PRG: Post-Redirect-Get)

    alumnos_data = []  # Lista que va a contener los datos procesados de cada alumno para la plantilla
    for alumno in alumnos:  # Itera cada alumno del curso
        evals_qs = alumno.evaluaciones.all()  # alumno.evaluaciones: RelatedManager que hace SELECT * FROM calificaciones_evaluacion WHERE alumno_id = alumno.id (usa el related_name="evaluaciones" del modelo)
        evals_dict = {e.tipo: e.valor for e in evals_qs}  # Dict comprehension: crea un diccionario { "TP 1": Decimal("8.50"), "Examen": Decimal("7.00") } para acceso rápido por tipo
        prom = obtener_promedio(evals_qs)  # Llama a la función auxiliar que calcula el promedio
        alumnos_data.append({  # Agrega un diccionario con los datos del alumno a la lista
            "alumno": alumno,  # El objeto Alumno completo (Django lo serializa en la plantilla)
            "evaluaciones": evals_dict,  # Diccionario para acceder con {{ evaluaciones|dictget:tipo }}
            "promedio": prom,  # Número: promedio del alumno
            "estado": obtener_estado(prom, alumno),  # String: TEA/TEP/TED (prioriza el estado manual del alumno si existe)
        })

    return render(request, "calificaciones/ver_curso.html", {  # Renderiza la plantilla con el contexto completo
        "curso": curso,
        "alumnos_data": alumnos_data,  # Lista de diccionarios, uno por alumno
        "tipos": tipos,  # QuerySet con los nombres de las columnas
    })


# ---------------------------------------------------------------------------
# PROFESOR: agregar una nueva columna de evaluación al curso
# ---------------------------------------------------------------------------

def agregar_evaluacion(request, curso_id):  # Crea un nuevo tipo de evaluación para TODOS los alumnos del curso (agrega una columna)
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == "POST":  # Si el profesor envió el formulario
        tipo = request.POST.get("tipo", "").strip()  # request.POST.get("tipo"): obtiene el valor del input llamado "tipo". El segundo argumento "" es el valor por defecto si la clave no existe
        if tipo:  # Si el nombre del tipo no está vacío
            for alumno in Alumno.objects.filter(curso=curso):  # Itera todos los alumnos del curso
                Evaluacion.objects.get_or_create(  # get_or_create: busca (alumno, tipo); si no existe, lo crea. Devuelve (objeto, creado_booleano)
                    alumno=alumno, tipo=tipo, defaults={"valor": None}  # defaults: solo se usa al CREAR. La nota se crea vacía (None)
                )
            messages.success(request, f"Columna '{tipo}' agregada para todos los alumnos.")
            return redirect("ver_curso", curso_id=curso_id)  # Vuelve a la grilla del curso
        messages.error(request, "Escribí un nombre para la evaluación.")
    return render(request, "calificaciones/agregar_evaluacion.html", {"curso": curso})


# ---------------------------------------------------------------------------
# PROFESOR: exportar curso a CSV
# ---------------------------------------------------------------------------

def exportar_csv(request, curso_id):  # Genera un archivo CSV con todas las notas del curso y lo devuelve como descarga
    curso = get_object_or_404(Curso, id=curso_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by("nombre")
    tipos = (
        Evaluacion.objects.filter(alumno__curso=curso)
        .values_list("tipo", flat=True)
        .distinct()
        .order_by("tipo")
    )

    safe = str(curso).replace("/", "-").replace("\\", "-").replace(":", "-")  # Reemplaza caracteres que no se pueden usar en nombres de archivo
    safe = "".join(c for c in safe if c.isalnum() or c in " _-").strip()  # isalnum(): letras y números. Filtra cualquier carácter que no sea alfanumérico, espacio, guión o guión bajo

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")  # HttpResponse: respuesta HTTP personalizada. content_type: declara que es un CSV con BOM UTF-8 (utf-8-sig agrega 3 bytes BOM al inicio, necesario para que Excel detecte UTF-8 correctamente)
    response["Content-Disposition"] = f'attachment; filename="{safe}.csv"'  # Content-Disposition: header HTTP que fuerza la descarga del archivo en vez de mostrarlo en el navegador. attachment = descargar. filename = nombre sugerido

    writer = csv.writer(response, lineterminator="\n")  # csv.writer: escribe filas CSV en el objeto response. lineterminator="\n": usa solo \n como fin de línea (Windows usa \r\n, pero esto evita líneas en blanco extra)
    writer.writerow(["Alumno", "DNI"] + list(tipos) + ["Promedio", "Estado"])  # writerow(): escribe una fila (lista) en el CSV. Primera fila = encabezados

    for alumno in alumnos:  # Por cada alumno, construye una fila con sus datos
        evals_qs = alumno.evaluaciones.all()
        evals = {e.tipo: e.valor for e in evals_qs}
        fila = [
            alumno.nombre,
            alumno.dni or "",  # Si no tiene DNI, escribe celda vacía
        ]
        for t in tipos:  # Para cada columna (tipo de evaluación)
            v = evals.get(t)  # Obtiene la nota del alumno para ese tipo
            fila.append(str(v) if v is not None else "")  # Si hay nota, la escribe; si no, celda vacía
        prom = obtener_promedio(evals_qs)
        fila.append(str(prom))
        fila.append(obtener_estado(prom, alumno))
        writer.writerow(fila)  # Escribe la fila en el CSV

    return response  # Django devuelve el HttpResponse como descarga de archivo (el navegador lo reconoce por el Content-Disposition)


# ---------------------------------------------------------------------------
# PROFESOR: importar CSV al curso
# ---------------------------------------------------------------------------

def importar_csv(request, curso_id):  # Importa alumnos y notas desde un archivo CSV subido por el profesor
    curso = get_object_or_404(Curso, id=curso_id)
    resultado = {"agregados": 0, "errores": []}  # Diccionario para acumular estadísticas de la importación

    if request.method == "POST" and request.FILES.get("archivo"):  # request.FILES: diccionario con los archivos subidos en el formulario (requiere enctype="multipart/form-data" en el HTML)
        archivo = request.FILES["archivo"]  # Obtiene el archivo subido (objeto UploadedFile, contenido en memoria o en disco temporal)
        try:
            contenido = archivo.read().decode("utf-8-sig").splitlines()  # read(): lee todo el archivo como bytes. decode("utf-8-sig"): decodifica a string usando UTF-8 con BOM (el BOM se ignora automáticamente). splitlines(): divide en lista de strings por saltos de línea
        except UnicodeDecodeError:  # Si el archivo no está en UTF-8 (ej: guardado como ANSI desde Excel)
            contenido = archivo.read().decode("latin-1").splitlines()  # Reintenta con latin-1 (ISO-8859-1, compatible con Windows-1252)

        reader = csv.DictReader(contenido)  # DictReader: lee el CSV y devuelve cada fila como un diccionario {nombre_columna: valor}. La primera fila se interpreta como encabezados
        for i, fila in enumerate(reader, start=2):  # enumerate(reader, start=2): i empieza en 2 porque la fila 1 son los encabezados. fila es un dict con los valores de cada columna
            nombre = fila.get("nombre", "").strip()  # Obtiene el valor de la columna "nombre". .get() con default "" evita KeyError si la columna no existe
            dni = fila.get("dni", "").strip()
            if not nombre:  # Si la fila no tiene nombre, no se puede crear el alumno
                resultado["errores"].append(f"Fila {i}: falta el nombre")
                continue  # Salta a la siguiente fila del CSV

            if dni and Alumno.objects.filter(dni=dni).exclude(  # Si hay DNI y existe otro alumno con ese mismo DNI
                nombre=nombre, curso=curso  # exclude(): excluye de la verificación al alumno que tiene (nombre, curso) iguales (para no marcar como duplicado al mismo alumno)
            ).exists():  # .exists(): más eficiente que .count() > 0, solo verifica existencia sin contar
                resultado["errores"].append(f"Fila {i}: DNI {dni} ya existe para otro alumno")
                continue

            alumno, creado = Alumno.objects.get_or_create(  # get_or_create devuelve (objeto, booleano: True si se creó)
                nombre=nombre, curso=curso, defaults={"dni": dni or None}
            )
            if creado:  # Si es un alumno nuevo
                resultado["agregados"] += 1  # Incrementa el contador de alumnos agregados
            elif dni:  # Si el alumno ya existía pero se especificó un DNI
                alumno.dni = dni  # Actualiza el DNI que podría haber estado vacío
                alumno.save(update_fields=["dni"])  # save(update_fields): solo actualiza el campo dni en BD (más eficiente y evita conflictos de concurrencia)

            for columna, valor in fila.items():  # Itera sobre todas las columnas de la fila CSV
                col = columna.strip()  # Limpia espacios en el nombre de la columna
                if col and col not in ("nombre", "dni", "Promedio", "Estado"):  # Salta las columnas no numéricas (no son tipos de evaluación)
                    nota = parsear_nota(valor) if valor.strip() else None  # Si hay valor, lo parsea; si no, None
                    try:
                        Evaluacion.objects.update_or_create(  # Igual que en ver_curso: actualiza o crea la evaluación
                            alumno=alumno, tipo=col, defaults={"valor": nota},
                        )
                    except Exception:
                        continue  # Ignora errores de evaluación específica

        if resultado["errores"]:  # Si hubo errores, muestra advertencia con resumen
            messages.warning(request, f"{resultado['agregados']} importados. {len(resultado['errores'])} error(es).")
        else:  # Si todo salió bien
            messages.success(request, f"{resultado['agregados']} alumnos importados correctamente.")
        return redirect("ver_curso", curso_id=curso_id)

    return render(request, "calificaciones/importar.html", {"curso": curso})  # GET: muestra el formulario de importación


# ---------------------------------------------------------------------------
# PROFESOR: agregar alumno
# ---------------------------------------------------------------------------

def agregar_alumno(request):  # Formulario para agregar un alumno a un curso existente. No recibe curso_id, el usuario selecciona el curso de un <select>
    error = ""  # String para mensaje de error de validación
    cursos = Curso.objects.all().order_by("-año", "curso", "division", "materia")  # Lista completa de cursos para el <select>

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        dni = request.POST.get("dni", "").strip()
        curso_id = request.POST.get("curso_id", "").strip()  # El <select> envía el ID del curso seleccionado

        if not nombre or not curso_id:  # Validación de campos obligatorios
            error = "Completá todos los campos obligatorios."
        elif dni and Alumno.objects.filter(dni=dni).exists():  # Si el DNI ya existe en la BD (en cualquier curso)
            error = f"El DNI {dni} ya está registrado para otro alumno."
        else:
            try:
                curso = Curso.objects.get(id=curso_id)  # Intenta obtener el curso; si el ID no es válido o no existe, lanza excepción
            except (Curso.DoesNotExist, ValueError):  # DoesNotExist: no hay curso con ese ID. ValueError: curso_id no es un número
                error = "Seleccioná un curso válido."
            else:  # Se ejecuta solo si el try fue exitoso (no se lanzó excepción)
                nombre_correcto = obtener_nombre_correcto(nombre)  # Busca capitalización correcta en BD
                existe = Alumno.objects.filter(  # Verifica si ya existe otro alumno con el mismo nombre en el mismo curso
                    nombre__iexact=nombre_correcto, curso=curso  # __iexact: lookup case-insensitive exact. SQL: UPPER(nombre) = UPPER('valor')
                ).exists()
                if existe:
                    error = "Ese alumno ya está en ese curso."
                else:
                    Alumno.objects.create(  # INSERT INTO calificaciones_alumno (nombre, curso_id, dni)
                        nombre=nombre_correcto,
                        curso=curso,
                        dni=dni or None,  # Si el DNI está vacío, guarda None
                    )
                    messages.success(request, f"Alumno '{nombre_correcto}' agregado a {curso}.")
                    return redirect("profesor")  # Vuelve al listado de cursos

    return render(request, "calificaciones/formulario_alumno.html", {
        "titulo": "Agregar alumno a un curso",
        "boton": "Guardar alumno",
        "error": error,
        "alumno": None,  # None indica que es creación (la plantilla usa esto para saber si es edición o creación)
        "cursos": cursos,
        "curso_selected_id": None,  # Para no preseleccionar ningún curso
    })


# ---------------------------------------------------------------------------
# PROFESOR: editar alumno
# ---------------------------------------------------------------------------

def editar_alumno(request, alumno_id):  # Formulario para editar un alumno existente. Recibe el ID del alumno desde la URL
    alumno = get_object_or_404(Alumno, id=alumno_id)  # Busca el alumno o 404
    error = ""
    cursos = Curso.objects.all().order_by("-año", "curso", "division", "materia")

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        dni = request.POST.get("dni", "").strip()
        curso_id = request.POST.get("curso_id", "").strip()

        if not nombre or not curso_id:
            error = "Completá todos los campos obligatorios."
        elif dni and Alumno.objects.filter(dni=dni).exclude(id=alumno_id).exists():  # exclude(id=alumno_id): permite mantener el mismo DNI del alumno que se está editando
            error = f"El DNI {dni} ya está registrado para otro alumno."
        else:
            try:
                curso = Curso.objects.get(id=curso_id)
            except (Curso.DoesNotExist, ValueError):
                error = "Seleccioná un curso válido."
            else:
                nombre_correcto = obtener_nombre_correcto(nombre)
                duplicado = (
                    Alumno.objects.filter(nombre__iexact=nombre_correcto, curso=curso)
                    .exclude(id=alumno_id)  # Excluye al alumno que se está editando (para evitar falsos duplicados)
                    .exists()
                )
                if duplicado:
                    error = "Ese alumno ya existe en ese curso."
                else:
                    alumno.nombre = nombre_correcto  # Modifica los atributos del objeto Python
                    alumno.dni = dni or None
                    alumno.curso = curso
                    alumno.save()  # save(): genera UPDATE en BD de todas las columnas que cambiaron
                    messages.success(request, "Alumno actualizado correctamente.")
                    return redirect("profesor")

    return render(request, "calificaciones/formulario_alumno.html", {
        "titulo": "Editar alumno",
        "boton": "Guardar cambios",
        "error": error,
        "alumno": alumno,  # Pasa el objeto Alumno para pre-llenar los campos del formulario
        "cursos": cursos,
        "curso_selected_id": alumno.curso.id,  # ID del curso actual para marcarlo como seleccionado en el <select>
    })


# ---------------------------------------------------------------------------
# PROFESOR: crear curso
# ---------------------------------------------------------------------------

def crear_curso(request):  # Formulario para crear un curso nuevo (vacío, sin alumnos)
    error = ""
    if request.method == "POST":
        curso_str = request.POST.get("curso", "").strip()
        division = request.POST.get("division", "").strip()
        materia = request.POST.get("materia", "").strip()
        año_str = request.POST.get("año", "").strip()
        profesor = request.POST.get("profesor", "").strip()
        if not curso_str or not division or not materia or not año_str:  # Valida que los campos obligatorios no estén vacíos
            error = "Completá todos los campos."
        else:
            try:
                año = int(año_str)  # Convierte a int; si no es un número válido, lanza ValueError
            except (ValueError, TypeError):  # TypeError: si año_str es None (no debería)
                error = "El año debe ser un número (ej: 2026)."
            else:
                curso, creado = Curso.objects.get_or_create(  # Busca por los 4 campos unique_together; si existe, no lo crea de nuevo
                    año=año, curso=curso_str, division=division, materia=materia,
                    defaults={"profesor": profesor or None},  # defaults: solo se usa si se CREA el curso (no si ya existe)
                )
                if not creado and profesor:  # Si el curso ya existía Y se pasó un nombre de profesor
                    curso.profesor = profesor  # Actualiza el profesor aunque el curso no sea nuevo
                    curso.save(update_fields=["profesor"])  # save parcial: solo actualiza la columna profesor
                if creado:
                    messages.success(request, f"Curso '{curso}' creado correctamente.")
                else:
                    messages.info(request, f"El curso '{curso}' ya existía.")  # messages.info: estilo informativo (azul)
                return redirect("profesor")
    return render(request, "calificaciones/crear_curso.html", {"error": error})


# ---------------------------------------------------------------------------
# PROFESOR: eliminar curso
# ---------------------------------------------------------------------------

def eliminar_curso(request, curso_id):  # Elimina un curso completo. Por CASCADE, elimina todos sus alumnos y evaluaciones
    curso = get_object_or_404(Curso, id=curso_id)
    nombre = str(curso)  # Guarda el nombre legible ANTES de borrar (después de borrar, el objeto no existe más)
    curso.delete()  # .delete(): DELETE FROM calificaciones_curso WHERE id = curso_id. La BD ejecuta ON DELETE CASCADE en las tablas hijas (alumnos, evaluaciones, mensajes, notas)
    messages.success(request, f"Curso '{nombre}' eliminado.")
    return redirect("profesor")


# ---------------------------------------------------------------------------
# PROFESOR: eliminar columna de evaluación
# ---------------------------------------------------------------------------

def eliminar_evaluacion(request, curso_id):  # Elimina todas las evaluaciones de un tipo específico para todo el curso
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == "POST":  # Solo acepta POST (por seguridad: eliminar por GET es peligroso porque un enlace podría borrar datos)
        tipo = request.POST.get("tipo", "").strip()
        if tipo:
            deleted, _ = Evaluacion.objects.filter(  # filter(): selecciona evaluaciones del curso con ese tipo
                alumno__curso=curso, tipo=tipo  # alumno__curso: JOIN a través de la FK alumno → curso
            ).delete()  # .delete(): DELETE con WHERE. Devuelve una tupla (cantidad, {modelo: cantidad_por_modelo})
            messages.success(request, f"Columna '{tipo}' eliminada ({deleted} nota(s)).")
    return redirect("ver_curso", curso_id=curso_id)


# ---------------------------------------------------------------------------
# PROFESOR: eliminar alumno
# ---------------------------------------------------------------------------

def eliminar_alumno(request, alumno_id):  # Elimina un alumno y sus evaluaciones por CASCADE
    alumno = get_object_or_404(Alumno, id=alumno_id)
    nombre = alumno.nombre
    curso_id = alumno.curso.id  # Guarda el ID del curso ANTES de borrar
    alumno.delete()  # DELETE FROM calificaciones_alumno WHERE id = alumno_id
    messages.success(request, f"Alumno '{nombre}' eliminado.")
    return redirect("ver_curso", curso_id=curso_id)  # Redirige a la grilla del curso al que pertenecía


# ---------------------------------------------------------------------------
# ALUMNO: formulario de consulta por DNI
# ---------------------------------------------------------------------------

def consultar(request):  # Página inicial para alumnos: ingresan su DNI para ver las notas
    dni = request.GET.get("dni", "").strip()  # request.GET.get(): obtiene el parámetro ?dni= de la URL (query string)
    if dni:  # Si ya hay un DNI en la URL (ej: /calificaciones/consultar/?dni=12345)
        return redirect("mis_notas?dni={dni}")  # Redirige directamente a la vista de notas con ese DNI
    return render(request, "calificaciones/consultar.html")  # Muestra el formulario vacío


# ---------------------------------------------------------------------------
# ALUMNO: ver solo mis notas (por DNI)
# ---------------------------------------------------------------------------

def mis_notas(request):  # Muestra las calificaciones del alumno cuyo DNI coincide con el parámetro GET
    dni = request.GET.get("dni", "").strip()
    if not dni:  # Si no hay DNI en la URL, redirige al formulario de consulta
        return redirect("consultar")

    alumnos = Alumno.objects.filter(dni=dni).select_related("curso")  # filter(dni): busca todos los alumnos con ese DNI. select_related("curso"): hace JOIN con la tabla Curso en la MISMA consulta SQL (evita N+1 queries, donde N=cantidad de alumnos)
    if not alumnos.exists():  # .exists(): consulta SQL EXISTS, más eficiente que .count() para solo verificar existencia
        return render(request, "calificaciones/mis_notas.html", {
            "error": f"No se encontró ningún alumno con DNI {dni}.",
            "alumno": None,
            "cursos_data": [],
            "promedio_general": 0,
            "estado_general": "",
            "dni": dni,
        })

    alumno = alumnos.first()  # .first(): devuelve el primer objeto del QuerySet o None si está vacío. Como ya verificamos exists(), acá habrá un objeto
    cursos_data = []

    for a in alumnos:  # Un mismo DNI puede corresponder a varios alumnos en diferentes cursos (raro pero posible)
        c = a.curso
        evals_qs = Evaluacion.objects.filter(alumno=a)  # SELECT WHERE alumno_id = a.id
        tipos = evals_qs.values_list("tipo", flat=True).distinct().order_by("tipo")
        evals_dict = {e.tipo: e.valor for e in evals_qs}
        prom = obtener_promedio(evals_qs)

        cursos_data.append({
            "curso": c,
            "evaluaciones": evals_dict,
            "tipos": list(tipos),
            "promedio": prom,
            "estado": obtener_estado(prom, a),
        })

    promedio_general = 0
    if cursos_data:
        promedio_general = round(  # Promedio de todos los promedios de materias
            sum(cd["promedio"] for cd in cursos_data) / len(cursos_data), 2
        )

    return render(request, "calificaciones/mis_notas.html", {
        "alumno": alumno,
        "cursos_data": cursos_data,
        "promedio_general": promedio_general,
        "estado_general": obtener_estado(promedio_general),  # Sin alumno, así que solo usa el promedio
        "error": None,
        "dni": dni,
    })


# ---------------------------------------------------------------------------
# ALUMNO: bandeja de mensajes
# ---------------------------------------------------------------------------

def mensajes(request):  # Muestra los mensajes que el profesor envió al curso del alumno
    dni = request.GET.get("dni", "")
    alumno = Alumno.objects.filter(dni=dni).first()  # .first(): obtiene el primer alumno con ese DNI o None (sin lanzar excepción)
    mensajes_qs = []  # Lista vacía por defecto
    if alumno:
        mensajes_qs = Mensaje.objects.filter(curso=alumno.curso)  # Solo muestra mensajes del curso del alumno encontrado
    return render(request, "calificaciones/mensajes.html", {
        "mensajes": mensajes_qs,
        "dni": dni,  # Se pasa el DNI para mantenerlo en los enlaces
    })


# ---------------------------------------------------------------------------
# PROFESOR: enviar mensaje a un curso (formulario + listado de enviados)
# ---------------------------------------------------------------------------

def enviar_mensaje(request, curso_id):  # Página unificada: muestra formulario para enviar mensaje y lista los ya enviados con opción de borrar
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == "POST":  # Si enviaron el formulario de nuevo mensaje
        titulo = request.POST.get("titulo", "").strip()
        contenido = request.POST.get("contenido", "").strip()
        if titulo and contenido:  # Ambos campos requeridos
            Mensaje.objects.create(  # INSERT INTO calificaciones_mensaje (curso_id, titulo, contenido)
                curso=curso, titulo=titulo, contenido=contenido  # creado se setea solo por auto_now_add
            )
            messages.success(request, f"Mensaje enviado a {curso}.")
        else:
            messages.error(request, "Completá título y contenido.")
    mensajes = Mensaje.objects.filter(curso=curso)  # SELECT * FROM calificaciones_mensaje WHERE curso_id=curso.id ORDER BY -creado (por Meta.ordering)
    return render(request, "calificaciones/enviar_mensaje.html", {
        "curso": curso, "mensajes": mensajes,
    })


def eliminar_mensaje(request, mensaje_id):  # Elimina un mensaje y redirige a la página de mensajes del mismo curso
    mensaje = get_object_or_404(Mensaje, id=mensaje_id)
    curso_id = mensaje.curso.id  # Guarda el curso antes de borrar el mensaje
    mensaje.delete()  # DELETE FROM calificaciones_mensaje WHERE id = mensaje_id
    messages.success(request, "Mensaje eliminado.")
    return redirect("enviar_mensaje", curso_id=curso_id)  # Vuelve a la página de mensajes del mismo curso


# ---------------------------------------------------------------------------
# PROFESOR: reportar alumno a dirección (formulario + listado + borrar)
# ---------------------------------------------------------------------------

def reportar_alumno(request, alumno_id):  # Página para reportar un alumno específico a dirección. Muestra formulario + lista de reportes del curso
    alumno = get_object_or_404(Alumno, id=alumno_id)
    curso = alumno.curso  # Obtiene el curso a través de la FK del alumno (alumno.curso_id)
    if request.method == "POST":
        asunto = request.POST.get("asunto", "").strip()
        mensaje = request.POST.get("mensaje", "").strip()
        if asunto and mensaje:
            NotaDireccion.objects.create(  # INSERT INTO calificaciones_notadireccion
                alumno=alumno, curso=curso,
                asunto=asunto, mensaje=mensaje
            )
            messages.success(request, f"Nota enviada a dirección sobre {alumno.nombre}.")
        else:
            messages.error(request, "Completá asunto y mensaje.")
    reportes = NotaDireccion.objects.filter(curso=curso).select_related("alumno")  # .select_related("alumno"): hace JOIN con la tabla Alumno en la misma consulta para evitar N+1 queries
    return render(request, "calificaciones/reportar_alumno.html", {
        "alumno": alumno, "curso": curso, "reportes": reportes,
    })


def eliminar_reporte(request, reporte_id):  # Elimina un reporte y redirige al listado de reportes del curso
    reporte = get_object_or_404(NotaDireccion, id=reporte_id)
    curso = reporte.curso
    reporte.delete()  # DELETE FROM calificaciones_notadireccion WHERE id = reporte_id
    messages.success(request, "Reporte eliminado.")
    return redirect("reportes_curso", curso_id=curso.id)  # Vuelve al listado de reportes del curso


def reportes_curso(request, curso_id):  # Muestra todos los reportes a dirección de un curso específico
    curso = get_object_or_404(Curso, id=curso_id)
    reportes = NotaDireccion.objects.filter(curso=curso).select_related("alumno")  # JOIN con alumno para mostrar el nombre
    return render(request, "calificaciones/reportes_curso.html", {
        "curso": curso, "reportes": reportes,
    })
