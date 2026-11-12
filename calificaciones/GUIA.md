# Guía de estudio — Módulo 3: Calificaciones

Esta guía es para **preparar la exposición** y entender el código antes de
defenderlo. La ficha técnica completa está en [`README.md`](README.md).

---

## 1. En una frase

Cada docente carga las notas de sus materias, la planilla oficial se completa
e imprime, y el alumno ve su boletín **solo cuando secretaría lo publica a fin
de año**.

---

## 2. Cómo levantarlo y probarlo

```bash
python manage.py migrate
python manage.py cargar_datos_demo
python manage.py runserver
```

Usuarios de prueba (clave `prueba1234`):

| Usuario | Rol | Para mostrar |
|---|---|---|
| `profesor1` | Docente (Ana Martínez) | cargar notas, categorías, planilla, cierre del cuatrimestre |
| `profesor2` | Docente (Carlos Russo) | que cada docente ve solo sus materias |
| `preceptora` | Secretaría | planillas de todos (solo lectura), boletines e interruptor anual |
| `acosta.lucia` | Alumna (5° B) | "Mis notas" y el boletín bloqueado hasta que se publique |

Recorrido sugerido para la exposición:

1. **`acosta.lucia`**: ve "Mis notas" y **no** tiene link al boletín. En Inglés
   tiene 8 pero dice "No acredita por asistencia" (70 %).
2. **`profesor1`**: entra a *Laboratorio de Programación* → *Cargar notas*,
   cambia una nota y se ve cómo la calificación se recalcula sola. Abre la
   *planilla*: la nota final aparece sola; prueba cargar una intensificación.
3. **`profesor1`**: cierra el 1° cuatrimestre desde la planilla. Vuelve a
   *Cargar notas*: la grilla quedó bloqueada. Reabre desde la planilla.
4. **`profesor2`**: no puede abrir materias de `profesor1` (cambiar el id en la
   URL lo devuelve a su inicio con un aviso).
5. **`preceptora`**: abre cualquier planilla en modo lectura y publica los
   boletines del año.
6. **`acosta.lucia`** otra vez: ahora aparece el boletín completo y puede
   registrar su firma.

---

## 3. Las reglas que hay que saber explicar

### 3.1 El boletín es anual y lo publica secretaría

- `PublicacionBoletin` (en `models.py`) es el interruptor: un registro por año
  con `publicado`, `fecha_publicacion` y `usuario`.
- Mientras no está publicado, el alumno ve solo "Mis notas" y el docente
  tampoco puede abrir boletines. Secretaría y directivo los ven siempre.
- El bloqueo está **en el servidor** (`alumno_ver_boletin` y `confirmar_rite`),
  no solo escondiendo el botón.

### 3.2 La calificación del cuatrimestre se pondera

- Cada columna de la grilla es una **categoría** (TP 1, Eval. 1…) con un
  **grupo** y un **peso %** (`CategoriaEvaluacion`).
- `_calificacion_cuat` promedia dentro de cada grupo y multiplica por el peso
  del grupo. Sin pesos, promedio simple.
- Ejemplo del demo: TP 1 = 8, TP 2 = 9 (Trabajos prácticos, 60 %) y
  Eval. 1 = 8 (40 %) → 8,3 → **8**.

### 3.3 Valoración TEA, TEP o TED

| Valoración | Nota | Color |
|---|---|---|
| TEA (Trayectoria Educativa Avanzada) | 7 a 10 | normal |
| TEP (Trayectoria Educativa en Proceso) | 5 a 6 | normal |
| TED (Trayectoria Educativa Discontinua) | 0 a 4 | rojo en "Mis notas", "Cargar notas" y boletín; **negro en la planilla oficial** |

La elige el docente en "Cargar notas"; si no la eligió, se deriva de la nota.

### 3.4 Con menos del 80 % de asistencia no se aprueba

- La cuenta está en `_asistencia_materia`. Total de clases = fechas con algún
  registro de la materia en el módulo Asistencia. Ausente = 1 falta,
  Tardanza = 0,5.
- Si la asistencia no llega, la materia dice **"No acredita por asistencia"**,
  la nota final de la planilla va en rojo y el boletín muestra un ⚠ sin
  promedio anual.

### 3.5 Cierre del cuatrimestre (uno por materia)

- El docente lo cierra desde la planilla: la calificación de cada alumno queda
  fija (`CierreCuatrimestre.calificacion`) con su fecha (`fecha_cierre`).
- Mientras está cerrado, "Cargar notas" es de solo lectura y no se puede
  importar Excel. Para corregir, el docente lo **reabre** desde la planilla.
- Cada materia tiene su propia fecha de cierre (se ve en el inicio del docente).

### 3.6 Intensificación y nota final

- **Intensificación del 1° cuatrimestre**: se carga en la planilla solo si el
  alumno no aprobó el 1° y al intensificar llegó a 7 o más.
- **Nota final**: aparece sola cuando los dos cuatrimestres tienen nota
  (promedio del 1° —o su intensificación— y el 2°). El docente la puede
  cambiar a mano; si la deja como está, se sigue calculando sola.

### 3.7 Quién puede hacer qué

| Acción | Docente | Secretaría | Directivo | Alumno |
|---|---|---|---|---|
| Cargar notas, categorías, Excel | sus materias | — | — | — |
| Planilla | editar las suyas | ver todas | ver todas | — |
| Boletín (publicado) | alumnos de sus cursos | todos, siempre | todos, siempre | el suyo |
| Firma "Adulta/o responsable" | sí | sí | sí | — |
| Firma "Director/a" | — | — | sí | — |
| Firma "Estudiante" | — | — | — | sí |
| Publicar el boletín del año | — | sí | sí | — |

---

## 4. La planilla: qué se edita y qué no

| Zona | ¿Se edita? | ¿Se guarda? |
|---|---|---|
| Turno y preceptor/a | Sí | Sí (`PlanillaDatos`) |
| Cursa / recursa, diciembre y febrero | Sí | Sí (`CierreCuatrimestre` del cuatrimestre que se mira) |
| Inasistencias de cada cuatrimestre | Sí | Sí (`InasistenciaMateria`) |
| Intensificación 1° cuatrimestre | Sí | Sí (`CierreCuatrimestre` del 1°) |
| Calificación final | Sí | Solo si se cambia (`CierreCuatrimestre` del 2°) |
| N° de orden, nombre y renglones en blanco | Sí, para imprimir | No |
| Notas parciales, valoración, calificaciones y totales | No: salen de "Cargar notas" | — |

---

## 5. Mapa del código

```
calificaciones/
├── models.py          # modelos propios (PublicacionBoletin, CierreCuatrimestre...)
├── views.py           # todas las pantallas, ordenadas por secciones
├── urls.py            # rutas: /calificaciones/profesor/<cuat>/<materia_id>/...
├── admin.py
├── tests.py           # tests de pantallas y reglas
├── tests_roles.py     # tests de permisos
├── management/commands/cargar_datos_demo.py
└── migrations/        # 0001 a 0009
templates/calificaciones/     # 11 plantillas, todas extienden base_cal.html
static/css/calificaciones.css # la única hoja de estilos del módulo
```

`views.py` está dividido en secciones con encabezados `# ─── ... ───`:

| Sección | Qué tiene |
|---|---|
| Helpers: rol, curso y permisos | quién es el usuario, qué materias puede ver o modificar, alumnos de un curso |
| Helpers: cálculo | `_calificacion_cuat`, `_valoracion_preliminar`, `_final_automatico` |
| Helpers: asistencia | `_asistencia_materia` (regla del 80 %) |
| Helpers: cierre | `_fecha_cierre` (si el cuatrimestre de una materia está cerrado) |
| Menú y publicación | inicio de cada rol e interruptor anual |
| Docente | cargar notas (+ guardado automático), categorías, Excel |
| Planilla | hoja oficial, guardar, cerrar y reabrir |
| Boletín | RITE, quién puede verlo y quién puede firmar |

**Dato para la defensa**: el módulo no modifica tablas de otros grupos. De
Alumnos lee `Alumno` (con `anio` y `division`) y `Curso`; de Docentes,
`Materia`; de Asistencia, los registros; de Cuentas, el rol del usuario.

---

## 6. Reparto del trabajo

| Parte | Integrante | Rama | Qué hizo |
|---|---|---|---|
| 1 | Seba | `seba` | Modelos y migraciones, diseño (base y CSS), menú por rol y boletín completo: publicación anual, RITE de frente y dorso, firmas y quién puede ver cada boletín |
| 2 | Lautaro | `lautaro` | Cargar notas con guardado automático, categorías e importación de Excel |
| 3 | Axel | `lerafer` | Planilla oficial: guardado, cierre y reapertura del cuatrimestre, intensificación y nota final |
| 4 | Kenai | `kenai` | Tests, datos de demostración y documentación |

---

## 7. Preguntas típicas de la defensa

- **¿Por qué el alumno no ve el boletín?** La publicación es anual y la
  controla secretaría con `PublicacionBoletin`; se valida en el servidor.
- **¿Qué pasa si un alumno tiene 8 pero faltó mucho?** No acredita: la regla
  del 80 % pisa a la nota.
- **¿Cómo se calcula la nota del cuatrimestre?** Ponderada por grupo y peso de
  las categorías; sin pesos, promedio simple.
- **¿Qué pasa al cerrar un cuatrimestre?** Las calificaciones quedan fijas y no
  se pueden cambiar notas hasta reabrirlo.
- **¿Por qué la URL tiene un número y no el nombre de la materia?** Porque dos
  cursos pueden tener una materia con el mismo nombre; el id no se repite.
- **¿De dónde salen las inasistencias?** De la carga del docente o, si no hay,
  del módulo Asistencia (solo lectura).

---

## 8. Tests

```bash
python manage.py test calificaciones    # tests del módulo
python manage.py test                   # todo el proyecto
```
