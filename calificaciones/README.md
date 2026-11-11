# Módulo 3 — Gestión de Calificaciones · SGE E.E.S.T. N°3

Ficha técnica del módulo. Es la referencia para cualquier técnico que tome el
proyecto: qué hace, cómo está armado, qué reglas de negocio aplica y cómo se
prueba. Para preparar la exposición, ver la [guía de estudio](GUIA.md).

- **Proyecto**: SGE (Sistema de Gestión Escolar) — Django 6 + SQLite
- **Módulo**: `calificaciones` (Módulo 3 del grupo)
- **Alcance**: el módulo **no** modifica alumnos, docentes ni asistencia: solo
  los consulta.

---

## 1. Qué hace el módulo

Carga y consulta de calificaciones de la escuela, con el diseño de las
maquetas del zip `diseno-sge-calificaciones`:

| Rol | Qué ve |
|---|---|
| **Docente** | Inicio con **sus** materias y el % de carga de cada una → carga notas → planilla del cuatrimestre → cierre. El boletín lo ve recién cuando está publicado. |
| **Alumno** | Inicio "Mis notas" (materia, valoración, calificación, estado, promedio, inasistencias). El boletín (documento imprimible de frente y dorso) recién aparece cuando secretaría lo publica a fin de año. |
| **Secretaría / preceptora** | Planillas de **todos** los docentes (para imprimir; cada una con el nombre de su docente) + buscador de alumno para ver su boletín + interruptor anual de publicación. |
| **Directivo** | Igual que secretaría: ve las planillas y los boletines siempre, y puede publicar u ocultar el boletín anual. |

Al iniciar sesión **todos** los usuarios caen en el inicio del sistema (`/`),
que muestra el acceso a todos los módulos.

### Permisos por rol

| Puede | Docente | Secretaría | Directivo | Alumno |
|---|---|---|---|---|
| Ver la planilla | solo de sus materias | de todas (solo lectura) | de todas (solo lectura) | — |
| Cargar notas / categorías / Excel | de sus materias | — | — | — |
| Guardar o cerrar un cuatrimestre | de sus materias | — | — | — |
| Ver el boletín | alumnos de sus cursos, solo si está publicado | siempre | siempre | solo el suyo y solo si está publicado |
| Registrar firma "Adulta/o responsable" | sí | sí | sí | — |
| Registrar firma "Director/a" | — | — | sí | — |
| Registrar firma "Estudiante" | — | — | — | la suya |
| Publicar / ocultar el boletín anual | — | sí | sí | — |

**Regla del boletín**: el alumno **nunca** puede abrir el boletín antes de fin de
año. Mientras no esté publicado, su inicio muestra el resumen "Mis notas" y un
aviso, sin link al boletín. La habilitación la hace secretaría o el directivo
con un interruptor anual (`PublicacionBoletin`). El bloqueo se aplica en el
servidor, no solo ocultando el botón: `alumno_ver_boletin` y `confirmar_rite`
redirigen al menú con el aviso "El boletín se habilita a fin de año".

Cada docente tiene su propio usuario: si un docente abre por URL la planilla
de una materia de otro, el sistema lo devuelve a su menú con el aviso "No podés
consultar esa materia". En la planilla siempre figura **el docente de esa
materia** (no quien la está mirando), así que la secretaría puede imprimir las
de todos.

---

## 2. Estructura del módulo

```
calificaciones/
├── models.py                    # 9 modelos (ver §3)
├── views.py                     # vistas por rol + endpoints AJAX
├── urls.py                      # 17 URLs por id de materia (ver §5)
├── admin.py                     # registro en el admin de Django
├── tests.py                     # tests de las pantallas
├── tests_roles.py               # tests de roles y permisos
├── README.md / GUIA.md          # ficha técnica y guía de estudio
├── management/commands/
│   └── cargar_datos_demo.py     # datos de ejemplo (idempotente)
├── migrations/                  # 0001 a 0009
└── templates/calificaciones/    # 11 plantillas (ver §6)
```

Además, fuera de la carpeta del módulo (pero del módulo):

- `templates/calificaciones/` — las plantillas
- `static/css/calificaciones.css` — la hoja de estilos

**El módulo no modifica ningún archivo de otro grupo.** De los otros módulos
solo *lee*:

| Módulo | Qué usa |
|---|---|
| `alumnos` | `Alumno` (nombre, apellido, DNI, `anio`, `division`, `activo`) y `Curso`. Los alumnos de un curso se buscan por `anio` + `division`, porque `Alumno` no tiene relación directa con `Curso`. |
| `docentes` | `Docente` y `Materia` (cada materia tiene su curso y su docente) |
| `asistencia` | `RegistroAsistencia` para inasistencias y la regla del 80 % |
| `cuentas` | `Perfil` (rol del usuario) y el decorador `rol_requerido` |

La barra superior muestra el link "Mi perfil" solo si el proyecto tiene la
ruta `perfil`; si no existe, muestra el usuario sin link (no da error).

---

## 3. Modelo de datos

| Modelo | Qué guarda | Relaciones |
|---|---|---|
| `CategoriaEvaluacion` | Categorías de evaluación de una materia: nombre, orden, **grupo** (agrupa columnas) y **peso** (%) | → `docentes.Materia` |
| `NotaEvaluacion` | La nota de un alumno en una categoría de un cuatrimestre (0 a 10) | → `alumnos.Alumno`, `docentes.Materia`, `CategoriaEvaluacion` |
| `CierreCuatrimestre` | Cierre de un alumno en una materia por cuatrimestre: valoración TEA/TEP/TED, cursada C/R, calificación oficial, intensificación, notas de diciembre/febrero, calificación final, estado "cerrado" y fecha de cierre. En el 1° cuatrimestre `calificacion_final` es la nota de intensificación; en el 2°, la final cargada a mano | → `alumnos.Alumno`, `docentes.Materia` |
| `InasistenciaMateria` | Inasistencias cargadas a mano por el docente para un alumno, materia y cuatrimestre (admite medias faltas) | → `alumnos.Alumno`, `docentes.Materia` |
| `ConfirmacionRite` | Quién tomó conocimiento del boletín y cuándo (director, adulto responsable o estudiante) | → `alumnos.Alumno` |
| `BoletinConfig` | Modelo viejo (una fecha de cierre para toda la escuela). **Ya no lo usa ninguna pantalla**: la fecha de cierre ahora va por materia en `CierreCuatrimestre`. Queda para no perder datos | — |
| `PublicacionBoletin` | Interruptor **anual** del boletín: año, si está publicado, fecha y usuario que lo cambió. Es la única fuente de verdad para que el alumno vea el boletín | — |
| `PlanillaDatos` | Turno y preceptor/a del encabezado de la planilla imprimible | → `docentes.Materia` |
| `Calificacion` | Modelo del esqueleto original (bimestre + nota). **No lo usa ninguna vista**: quedó por compatibilidad con el esqueleto | → `alumnos.Alumno`, `docentes.Materia` |

Restricción del proyecto: **las claves foráneas solo apuntan a
`alumnos.Alumno` y `docentes.Materia`** (para no romper el merge con los otros
grupos). Por eso `ConfirmacionRite.usuario` es un texto, no una FK a `User`.

---

## 4. Reglas de negocio

**Calificación del cuatrimestre** (`_calificacion_cuat` en `views.py`)

1. Si las categorías tienen **peso**, se calcula ponderada: las categorías con
   el mismo `grupo` se promedian entre sí (usando su peso) y ese resultado se
   multiplica por el peso del grupo; al final se divide por la suma de pesos.
   Ejemplo del demo: TP 1 (30 %) + TP 2 (30 %) + Eval. 1 (40 %) → 8,3 → **8**.
2. Si **no** hay pesos, es el promedio simple de las notas cargadas.
3. Si faltan notas de una categoría, esa categoría no cuenta; si falta un grupo
   entero, su peso no cuenta.
4. La calificación que se muestra es un entero (redondeo medio hacia arriba).

**Estado de una materia** (`_estado_materia`): **7 o más → "Aprobada"**, menos
de 7 → **"A intensificar"**. Si la asistencia anual de la materia es menor al
80 %, el estado pasa a **"No acredita por asistencia"** aunque la nota sea 7 o
más (ver más abajo).

**Regla del 80 % de asistencia** (`_asistencia_materia`): con menos del 80 % de
asistencia en una materia **no se puede aprobar** esa materia. El total de clases
se toma de las fechas con algún registro de la materia en el módulo Asistencia
(así una falta no achica el denominador); Ausente = 1 falta y Tardanza = 0,5. Si
la materia todavía no tiene registros de asistencia, la regla no restringe. Se
aplica en el menú del alumno, en la carga de notas, en la planilla y en el
boletín. En la planilla y el boletín la nota final se sigue mostrando, pero en
rojo y sin contar como aprobada; en el boletín se oculta el promedio anual y se
agrega un ⚠ junto a la materia.

**TED en rojo**: la valoración TED (0 a 4) se muestra en rojo (`.ted` en
`static/css/calificaciones.css`) en "Mis notas", en "Cargar notas" y en el
boletín. **En la planilla oficial va en negro**, como la hoja impresa. En la
planilla solo se marca en rojo la nota final de un alumno que no llega al 80 %
de asistencia (`.no-acredita`).

**Valoración preliminar** (TEA / TEP / TED): la elige el docente con un select
en "Cargar notas" y se guarda en el `CierreCuatrimestre`. Si todavía no hay
valoración cargada, se deriva de la nota: ≥ 7 → TEA, 5 o 6 → TEP, < 5 → TED.

**Cursada C/R** (columna del boletín): **C** = cursa por primera vez,
**R** = recursa.

**Inasistencias**: se leen del módulo `asistencia` (solo lectura, nunca se
tocan). Un Ausente = 1 falta, una Tardanza = media falta. Como Asistencia no
tiene cuatrimestre, se reparte por meses: **1° cuatrimestre = marzo a julio**,
**2° cuatrimestre = agosto a diciembre**. El docente también puede cargarlas a
mano en "Cargar notas" o en la planilla (`InasistenciaMateria`); si hay carga
manual, esa manda en las dos pantallas.

**Promedio anual** (boletín): promedio de ambos cuatrimestres **solo si los
dos son 7 o más** y la asistencia anual llega al 80 %; si no, queda en blanco.

**Calificación final de la planilla** (`_final_automatico` y
`_calificacion_final`): aparece sola cuando **los dos cuatrimestres tienen
calificación**: promedio del 1° cuatrimestre (o su intensificación, si la hubo)
y el 2°, redondeado a entero. El docente la puede cambiar a mano en la
planilla; solo se guarda si es distinta de la automática (se guarda en
`calificacion_final` del 2° cuatrimestre) y, si se vacía, vuelve a calcularse
sola. Con asistencia insuficiente se sigue mostrando, pero en rojo y sin
contar como aprobada.

**Intensificación del 1° cuatrimestre**: el docente la carga en la planilla.
Solo se acepta si el alumno **no** aprobó el 1° cuatrimestre y la nota es de 7
a 10 (si no, la planilla avisa y no la guarda). Se guarda en el cierre del 1°
cuatrimestre (`intensificacion` + `calificacion_final`).

**Planilla editable sin cambiar el diseño** (`profesor_planilla` +
`planilla.html`):

- **Se editan y se guardan**: cursada (C/R), inasistencias de cada
  cuatrimestre, intensificación del 1° cuatrimestre, diciembre, febrero y la
  calificación final (solo si se cambia). El encabezado (turno y preceptor/a)
  también se guarda en `PlanillaDatos`.
- **Se editan solo para imprimir** (no se guardan en la base): número de orden y
  apellido/nombre del alumno, y todas las casillas de los renglones en blanco
  de la hoja oficial (hasta el 37).
- Secretaría y directivo la ven en **modo lectura**: sin botones de guardar y
  con las casillas bloqueadas.
- **No se editan** (son calculadas): parciales, valoración preliminar,
  calificación de cada cuatrimestre, totales y clases.

**Cierre del cuatrimestre** (planilla del docente, uno **por materia**):
congela la calificación oficial de cada alumno (`CierreCuatrimestre.cerrado` +
`calificacion`) y guarda la fecha (`fecha_cierre`), que se muestra en la
tarjeta de esa materia en el inicio del docente. Mientras está cerrado:

- "Cargar notas" queda de solo lectura y los guardados automáticos responden
  error 409;
- no se puede importar Excel;
- no se puede borrar una categoría que tenga notas de ese cuatrimestre.

El docente lo **reabre** desde la planilla (botón "Reabrir"): las
calificaciones vuelven a calcularse con las notas. El cierre **no** habilita el
boletín del alumno.

**Publicación anual del boletín** (`PublicacionBoletin`): la activan secretaría
o el directivo desde el menú con el botón "Publicar boletines del año".
Mientras esté oculta, ni el alumno ni el docente pueden abrir el boletín; el
alumno sigue viendo su resumen "Mis notas". El año es el año calendario
(`timezone.now().year`), igual que el "Ciclo lectivo" de las pantallas. El
boletín se puede volver a ocultar con el mismo botón.

---

## 5. URLs

Las pantallas del docente llevan el **cuatrimestre** (1 o 2) y el **id de la
materia**. Se usa el id y no el nombre porque dos cursos pueden tener una
materia con el mismo nombre (por ejemplo, "Inglés" en 5° A y 5° B).

Ejemplo: `/calificaciones/profesor/1/7/planilla-calificaciones/`

| URL (después de `/calificaciones/profesor/<cuat>/<materia_id>/`) | Vista | Rol | Qué hace |
|---|---|---|---|
| `planilla-calificaciones/` | `profesor_planilla` | docente, secretaría, directivo | Planilla oficial (hoja oficio vertical) |
| `cargar-notas/` | `profesor_cargar_notas` | docente | Cargar notas (guardado automático) |
| `guardar-nota/` | `profesor_guardar_nota` | docente | **AJAX** guardar una nota |
| `guardar-valoracion/` | `profesor_guardar_valoracion` | docente | **AJAX** guardar TEA/TEP/TED |
| `guardar-inasistencia/` | `profesor_guardar_inasistencia` | docente | **AJAX** guardar inasistencias |
| `categorias/` | `profesor_categorias` | docente | Categorías de evaluación (grupo y peso) |
| `categorias/agregar/` | `profesor_agregar_categoria` | docente | **POST** crear categoría |
| `categorias/<id>/editar/` | `profesor_editar_categoria` | docente | **POST** editar categoría |
| `categorias/<id>/eliminar/` | `profesor_eliminar_categoria` | docente | **POST** eliminar categoría (con confirmación) |
| `excel/` | `profesor_cargar_excel` | docente | Subir Excel y ver la vista previa |
| `excel/confirmar/` | `profesor_confirmar_excel` | docente | **POST** guardar lo importado |
| `excel/plantilla/` | `profesor_descargar_plantilla` | docente | Descargar plantilla Excel |

| URL | Vista | Rol | Qué hace |
|---|---|---|---|
| `/calificaciones/` | `menu` | todos | Inicio según el rol |
| `/calificaciones/publicar-boletines/` | `publicar_boletines` | secretaría, directivo | **POST** publica u oculta el boletín del año |
| `/calificaciones/alumno/seleccionar/` | `alumno_seleccionar` | docente, secretaría, directivo | Elegir alumno para ver su boletín |
| `/calificaciones/boletin/` | `alumno_ver_boletin` | todos (según publicación) | Boletín del alumno (imprimible) |
| `/calificaciones/boletin/confirmar/` | `confirmar_rite` | todos (según publicación) | **POST** registrar firma de que tomó conocimiento |

**Navegación del docente**: Inicio → Cargar notas ⇄ Planilla. Desde Cargar
notas se entra a Categorías e Importar Excel, y su botón "← Volver a
&lt;materia&gt;" vuelve a Cargar notas.

### Contrato de los endpoints AJAX

`POST .../guardar-nota/` → `{"alumno_id": 1, "cat_id": 3, "valor": "8"}`

```json
{ "ok": true, "calificacion": "8", "estado_materia": "Aprobada" }
```

`POST .../guardar-valoracion/` → `{"alumno_id": 1, "valoracion": "TEA"}`

```json
{ "ok": true, "valoracion": "TEA" }
```

Todos devuelven `{"ok": false, "error": "..."}` si algo falla: 400 si el dato
no es válido, 403 si la materia no es del docente y 404 si el alumno no es del
curso. La planilla guarda con un POST normal (`accion=guardar` o
`accion=cerrar`) y el botón "Cerrar {n}° cuatrimestre" pide confirmación.

---

## 6. Plantillas y sistema de diseño

| Plantilla | Pantalla |
|---|---|
| `base_cal.html` | Shell común: barra de navegación y footer idénticos a los demás módulos (misma estética que `base.html`) |
| `menu_docente.html` | Inicio del docente |
| `menu_alumno.html` | Inicio del alumno ("Mis notas") |
| `menu.html` | Menú de consulta para administrativos |
| `cargar_notas.html` | Cargar notas (grilla con guardado automático) |
| `planilla.html` | Planilla del docente (Main) |
| `boletin.html` | Boletín del alumno: frente + dorso, listo para imprimir |
| `alumno_seleccionar.html` | Buscador de alumno |
| `gestionar_categorias.html` | Categorías de evaluación (grupo y peso) |
| `cargar_excel.html`, `confirmar_excel.html` | Importación de notas por Excel |

**Reglas de diseño**

- Las pantallas del módulo son *standalone*: usan `base_cal.html` y **no** el
  `templates/base.html` del proyecto. Las once pantallas del módulo (menús,
  carga de notas, planilla, boletín, categorías, Excel) comparten ese shell.
- El shell **replica la barra de navegación y el footer de `base.html`** (mismo
  logo, mismos módulos, mismos mensajes) para que el módulo tenga la **misma
  estética** que el resto del sistema. Sus estilos están copiados dentro de
  `static/css/calificaciones.css` (no se carga `base.css`) para mantener el
  módulo aislado y no generar conflictos al integrarlo con los otros módulos.
- `static/css/calificaciones.css` es la **única hoja de estilos del módulo**.
  Todas las pantallas usan los mismos componentes (sin estilos sueltos en cada
  plantilla):

  | Clase | Qué es |
  |---|---|
  | `.hero` (+ `.miga`, `.hero-sub`, `.hero-acciones`) | Encabezado celeste de cada pantalla: miga de pan, título y botones |
  | `.card` + `.tarjeta` (`.borde-azul`, `.borde-verde`, `.borde-rojo`, `.borde-oscuro`) | Tarjeta blanca con borde de color arriba |
  | `.grid-tarjetas`, `.stats`, `.dos-columnas` | Grillas que se acomodan solas al ancho de la pantalla |
  | `.btn` / `.btn.p` / `.btn.chico` / `.btn.peligro` | Botones (contorno, azul, chico, borrar) |
  | `.chip` + `.ok` `.wa` `.ne` | Etiquetas de estado |
  | `.tabla` (+ `.tabla-wrap`) | Tabla dentro de una tarjeta, con scroll horizontal si no entra |
  | `.form` | Formulario: igual que el resto del sistema |
  | `.ted`, `.no-acredita` | Rojo para TED y para lo que no acredita por asistencia |
  | `.seccion-titulo`, `.ayuda`, `.nota` | Títulos y textos de aclaración |

- Hay dos tipos de pantalla, y ambas usan los mismos componentes:
  - **Listado** (menús): título + subtítulo + botones de cuatrimestre + tarjetas.
  - **Detalle** (cargar notas, categorías, Excel): migas de pan + título +
    botón de volver + tarjeta.
- La **planilla** del docente es una **hoja imprimible de oficio vertical**
  (216 × 340 mm) con su propio CSS, como en la maqueta `planilla-docente`:
  membrete con los datos de la escuela, la materia, el profesor/a, el año y la
  sección; la tabla con los dos cuatrimestres, la intensificación y la
  calificación final; las tablas de totales; y las consideraciones legales.
  Se imprime con el botón "Imprimir (oficio vertical)"; en pantalla se ve como
  una hoja sobre fondo gris y al imprimir solo queda la hoja.
- El **boletín** del alumno también es un documento imprimible (frente y dorso):
  usa el shell en pantalla y al imprimir solo queda la hoja.
- Formato numérico es-AR (coma decimal) en todo lo que ve el usuario.

---

## 7. Puesta en marcha

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear la base y aplicar migraciones
python manage.py migrate

# 3. (Opcional) datos de demostración
python manage.py cargar_datos_demo

# 4. Levantar el servidor
python manage.py runserver
```

Usuarios que crea el comando de demostración (clave `prueba1234`):

| Usuario | Rol | Entra a |
|---|---|---|
| `profesor1` | docente — Ana Martínez | sus 3 materias de programación (5° B y 5° A) |
| `profesor2` | docente — Carlos Russo | sus 4 materias de 5° B (Historia, Inglés, Análisis, Teleinformática) |
| `preceptora` | secretaría — Paula Sosa | las planillas de **todos** los docentes, los boletines y el interruptor anual de publicación |
| `acosta.lucia` | alumno — Acosta, Lucía | Sus notas; el boletín aparece cuando la preceptora lo publica |

> Con los dos usuarios de docente se puede comprobar que cada uno ve solo sus
> materias y que el nombre que figura en la planilla es el del docente de esa
> materia.

> El comando `cargar_datos_demo` **borra y recrea solo sus propios datos**
> (identificados por DNI y nombre de usuario): se puede correr las veces que
> haga falta. No borra cursos, materias ni alumnos cargados por otros módulos;
> si los cursos 5° A y 5° B ya existen, los reutiliza.

> Importar y descargar Excel necesita la librería `openpyxl`
> (`pip install openpyxl`). No está en `requirements.txt` porque ese archivo es
> compartido; sin la librería, el resto del módulo funciona y esas dos
> pantallas avisan qué instalar.

---

## 8. Tests

```bash
python manage.py test calificaciones          # 72 tests
python manage.py test calificaciones.tests_roles
```

Qué cubren:

- **`tests.py`** — menús por rol, carga de notas (guardado automático,
  ponderación, coma decimal, Excel, botones de volver), planilla del docente
  (URL, guardado, cierre y reapertura, inasistencias, intensificación, nota
  final automática y a mano, celdas editables, modo lectura, TED en negro),
  materias con el mismo nombre en dos cursos, permisos de firmas y de boletín,
  boletín del alumno (frente + dorso, firmas de ambos cuatrimestres, TED y aviso
  por asistencia) y la publicación anual del boletín (alumno y docente
  bloqueados, secretaría y directivo siempre habilitados, interruptor). Incluye
  los tests de la regla del 80 % de asistencia.
- **`tests_roles.py`** — permisos: el administrativo no entra a cargar notas,
  el alumno no entra al buscador, el alumno solo ve su propia ficha aunque le
  manden el `alumno_id` de otro, el docente entra a su planilla.

---

## 9. Migraciones

| Migración | Qué hace |
|---|---|
| `0001_initial` | Modelo `Calificacion` (del esqueleto) |
| `0002_boletinconfig_categoriaevaluacion_notaevaluacion` | `BoletinConfig`, `CategoriaEvaluacion`, `NotaEvaluacion` |
| `0003_categoriaevaluacion_grupo_categoriaevaluacion_peso_and_more` | `grupo` y `peso` en las categorías + modelo `CierreCuatrimestre` |
| `0004_cierrecuatrimestre_cursada` | Campo `cursada` (C/R) |
| `0005_alter_cierrecuatrimestre_cursada_confirmacionrite` | Etiquetas de `cursada` + modelo `ConfirmacionRite` |
| `0006_inasistenciamateria` | Modelo `InasistenciaMateria` |
| `0007_planilladatos` | Modelo `PlanillaDatos` (turno y preceptor/a) |
| `0008_publicacionboletin` | Modelo `PublicacionBoletin` (interruptor anual del boletín) |
| `0009_cierrecuatrimestre_fecha_cierre` | Fecha de cierre por materia en `CierreCuatrimestre` |

---

## 10. Reglas para seguir trabajando

1. **No tocar otros módulos**: `alumnos`, `docentes`, `asistencia`, `core`,
   `comunicados`, `cuentas` ni `sge/`. Solo `calificaciones/`,
   `templates/calificaciones/` y `static/css/calificaciones.css`.
2. **Solo claves foráneas a `alumnos.Alumno` y `docentes.Materia`** (y a los
   modelos del propio módulo).
3. **Asistencia es de solo lectura**: el módulo calcula inasistencias a partir
   de sus registros, nunca los escribe.
4. Los mensajes al usuario van en español con **voseo**.
5. Los números que se muestran al usuario van con **coma decimal** (`_formato_ar`).
6. Al tocar una plantilla, probarla en el navegador con **Ctrl+F5** (el
   servidor con `--noreload` cachea plantillas en memoria: si cambiás código
   Python, reiniciá el servidor).

---

## 11. Pendientes conocidos

- "Imprimir / guardar como PDF" usa la impresión del navegador (se puede elegir
  "Guardar como PDF"); no hay generación de PDF en el backend.
- La secretaría puede ver las planillas de todos los docentes, pero no
  modificarlas; si hace falta que pueda corregir una carga, hay que darle
  también el rol docente o habilitarle la edición.
- Las pantallas de categorías y de Excel no tienen maqueta en el zip: están
  hechas con el mismo shell y estilo que el resto, pero su contenido es
  propuesta propia.
- `openpyxl` (para Excel) no está en `requirements.txt` porque es un archivo
  compartido: hay que instalarlo a mano. Sin la librería, la pantalla de Excel
  lo avisa.
- `Calificacion` (por bimestres) y `BoletinConfig` no los usa ninguna
  pantalla; quedan para no romper el esqueleto ni perder datos.
- Los "saberes pendientes" del dorso del boletín se completan a mano.
