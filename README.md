# Módulo 3 (Calificaciones): cómo sube cada uno su parte

El módulo está terminado y dividido en **4 features**, una por integrante.
Cada parte ya está en su rama del **repo del grupo**:
`https://github.com/sebaemaa/Modulo-calificaciones-g3`

Cada uno la lleva **desde su máquina** al **repo del profe**
(`https://github.com/eest3-hurlingham/sge-modulo3`), a su rama, y abre un Pull
Request hacia `dev`. El commit queda **a tu nombre**. Después los 4 PR se
mergean **en orden** (está explicado en `calificaciones/ORDEN_DE_MERGE.md`, que
viene en la parte de Seba). **Nadie mergea su propio PR**: lo revisa y lo
mergea otro integrante (regla 9).

> ## 🔄 Actualización del 12/11 (leer primero)
> El profe revisó el PR de Seba y pidió **un cambio**: sacar la tabla
> `InasistenciaMateria`, porque duplicaba datos del módulo Asistencia. Ahora
> las inasistencias **solo se muestran** (salen de Asistencia) y ya no se
> cargan a mano ni en "Cargar notas" ni en la planilla.
>
> - **Seba:** ya subió el cambio a `seba` (migración nueva `0010`).
> - **Lautaro:** ya habías subido tu parte, así que tenés que **actualizarla**
>   (pasos en "2. Lautaro" más abajo). Después abrí tu PR si todavía no lo
>   hiciste, y revisá y mergeá el PR de Seba.
> - **Axel y Kenai:** todavía no subieron; sigan sus pasos de abajo, que ya
>   traen el cambio. Esperen a que Lautaro avise que actualizó.
>
> Las ramas del repo del grupo ya tienen todo corregido. Los comandos cambiaron
> un poco respecto de la versión anterior de este instructivo: usen estos.

| Orden | Quién | Rama | Qué trae |
|---|---|---|---|
| 1 | Seba | `seba` | Modelos y migraciones, diseño del módulo, menú según el rol y boletín completo (publicación anual, RITE, firmas y permisos) |
| 2 | Lautaro | `lautaro` | Cargar notas (guardado automático), categorías de evaluación e importación de Excel |
| 3 | Axel | `lerafer` | Planilla de calificaciones (hoja oficial): cierre y reapertura del cuatrimestre, intensificación y nota final |
| 4 | Kenai | `kenai` | Tests y comando de datos de demostración |

Las partes solo tocan archivos del módulo (`calificaciones/`,
`templates/calificaciones/` y `static/css/calificaciones.css`). No modifican
nada de los otros grupos.

> ## ⚠ Cómo funciona el orden
> Cada parte usa código de la anterior, así que **cada uno arma su rama encima
> de la rama del compañero anterior** en el repo del profe. No hace falta
> esperar a que se mergee el anterior: **solo que el anterior ya haya hecho su push**.
>
> **Seba → Lautaro → Axel → Kenai**
>
> Cuando hagas tu push, avisale al siguiente por el grupo. Pueden hacerlo los
> cuatro el mismo día, uno detrás del otro.

---

## Antes de empezar (una sola vez)

Tenés que tener Git instalado y tu usuario configurado:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu-mail@ejemplo.com"
```

Y clonar el repo del profe, sumando el del grupo como segundo remoto:

```bash
git clone https://github.com/eest3-hurlingham/sge-modulo3.git
cd sge-modulo3
git remote add grupo https://github.com/sebaemaa/Modulo-calificaciones-g3.git
```

---

## Qué hace cada uno

Todos arrancan trayendo lo último de los dos repos:

```bash
git fetch origin
git fetch grupo
```

### 1. Seba (`seba`) — ya está hecho
La parte 1 y el cambio que pidió el profe ya están en `seba` del repo del profe
(PR #4). No hay que hacer nada.

### 2. Lautaro (`lautaro`) — actualizar lo que ya subiste
```bash
git checkout lautaro
git pull origin lautaro
git merge --no-commit origin/seba
git checkout grupo/lautaro -- calificaciones templates static/css/calificaciones.css
git commit -m "fix(calificaciones): las inasistencias se leen del modulo Asistencia"
git push origin lautaro
```
Este push va **sin** `--force`. Si `git merge` dice "Already up to date", igual
seguí con los pasos siguientes. Abrir PR `lautaro` → `dev` (si no lo abriste) y
avisarle a Axel.

### 3. Axel (`lerafer`), cuando Lautaro ya actualizó
```bash
git checkout -B lerafer origin/lautaro
git checkout grupo/lerafer -- calificaciones templates static/css/calificaciones.css
git commit -m "feat(calificaciones): planilla de calificaciones, cierre e intensificacion"
git push --force origin lerafer
```
Abrir PR `lerafer` → `dev`. Avisarle a Kenai.

### 4. Kenai (`kenai`), cuando Axel ya hizo su push
```bash
git checkout -B kenai origin/lerafer
git checkout grupo/kenai -- calificaciones templates static/css/calificaciones.css
git commit -m "feat(calificaciones): tests y datos de demostracion"
git push --force origin kenai
```
Abrir PR `kenai` → `dev`. Con esto están las 4 partes subidas.

El `--force` de Axel y Kenai es porque sus ramas en el repo del profe tienen
código viejo que hay que reemplazar. Lautaro no lo necesita.

> Fijate que en `git checkout -B` **cada uno parte de la rama del anterior**
> (`origin/seba`, `origin/lautaro`, `origin/lerafer`), no de `dev`. Si el
> anterior todavía no hizo su push, esa rama no existe o tiene código viejo:
> esperá su aviso.

**Para que el PR se vea prolijo:** hasta que se mergeen los anteriores,
tu PR va a mostrar también los cambios de los compañeros previos. Es normal:
cuando se mergea el anterior, GitHub actualiza tu PR y muestra solo lo tuyo.
En la descripción del PR podés poner: *"Va después del PR de `<rama anterior>`.
Orden de merge en `calificaciones/ORDEN_DE_MERGE.md`."*

---

## Para quien mergea (lo explica también ORDEN_DE_MERGE.md)

- Mergear en orden: `seba` → `lautaro` → `lerafer` → `kenai`.
- Usar **"Create a merge commit"**. **No** "Squash and merge" ni "Rebase and
  merge": como cada rama trae las anteriores, al aplastar commits el PR
  siguiente da conflicto.

---

## Si algo sale mal

- **Te quedó algo raro a mitad de camino:** casi siempre es porque partiste de
  la rama equivocada o el anterior todavía no hizo su push. Hacé
  `git fetch origin` y `git fetch grupo` y repetí desde `git checkout -B ...`
  (Lautaro: `git merge --abort` y repetir desde el principio).
- **`git push` pide permiso o falla:** tenés que ser colaborador del repo del
  profe; pedíselo.
- **Plan B:** en la carpeta `patches/` de esta rama están los mismos cambios
  como archivos `.patch`. En vez del `git checkout grupo/... -- ...` se puede hacer
  `git apply parte-N-<nombre>.patch` (con el archivo copiado en la carpeta del
  repo) y después `git add -A`.

---

## Probar que anda (con las 4 partes)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_datos_demo
python manage.py test calificaciones     # tienen que dar OK
python manage.py runserver
```

Usuarios de prueba (clave `prueba1234`): `profesor1` y `profesor2` (docentes),
`preceptora` (secretaría) y `sebaema` (alumna). Para importar o descargar
Excel hace falta `pip install openpyxl`.
