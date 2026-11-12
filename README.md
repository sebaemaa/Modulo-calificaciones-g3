# Módulo 3 (Calificaciones): cómo sube cada uno su parte

El módulo está terminado y dividido en **4 features**, una por integrante.
Cada parte ya está en su rama del **repo del grupo**:
`https://github.com/sebaemaa/Modulo-calificaciones-g3`

Cada uno la lleva **desde su máquina** al **repo del profe**
(`https://github.com/eest3-hurlingham/sge-modulo3`), a su rama, y abre un Pull
Request hacia `dev`. El commit queda **a tu nombre**. Después **el profe
mergea los 4 PR en orden** (está explicado en `calificaciones/ORDEN_DE_MERGE.md`,
que viene en la parte de Seba).

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
> esperar a que el profe mergee: **solo que el anterior ya haya hecho su push**.
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

### 1. Seba (`seba`), empieza primero
```bash
git checkout -B seba origin/dev
git cherry-pick --no-commit grupo/seba
git commit -m "feat(calificaciones): base del modulo, menu por rol y boletin RITE"
git push --force origin seba
```
Abrir PR `seba` → `dev` en el repo del profe. Avisarle a Lautaro.

### 2. Lautaro (`lautaro`), cuando Seba ya hizo su push
```bash
git checkout -B lautaro origin/seba
git cherry-pick --no-commit grupo/lautaro
git commit -m "feat(calificaciones): carga de notas, categorias e importacion de Excel"
git push --force origin lautaro
```
Abrir PR `lautaro` → `dev`. Avisarle a Axel.

### 3. Axel (`lerafer`), cuando Lautaro ya hizo su push
```bash
git checkout -B lerafer origin/lautaro
git cherry-pick --no-commit grupo/lerafer
git commit -m "feat(calificaciones): planilla de calificaciones, cierre e intensificacion"
git push --force origin lerafer
```
Abrir PR `lerafer` → `dev`. Avisarle a Kenai.

### 4. Kenai (`kenai`), cuando Axel ya hizo su push
```bash
git checkout -B kenai origin/lerafer
git cherry-pick --no-commit grupo/kenai
git commit -m "feat(calificaciones): tests y datos de demostracion"
git push --force origin kenai
```
Abrir PR `kenai` → `dev`. Con esto están las 4 partes subidas.

> Fijate que en `git checkout -B` **cada uno parte de la rama del anterior**
> (`origin/seba`, `origin/lautaro`, `origin/lerafer`), no de `dev`. Si el
> anterior todavía no hizo su push, esa rama no existe o tiene código viejo:
> esperá su aviso.

**Para que el PR se vea prolijo:** hasta que el profe mergee los anteriores,
tu PR va a mostrar también los cambios de los compañeros previos. Es normal:
cuando se mergea el anterior, GitHub actualiza tu PR y muestra solo lo tuyo.
En la descripción del PR podés poner: *"Va después del PR de `<rama anterior>`.
Orden de merge en `calificaciones/ORDEN_DE_MERGE.md`."*

---

## Para el profe (lo explica también ORDEN_DE_MERGE.md)

- Mergear en orden: `seba` → `lautaro` → `lerafer` → `kenai`.
- Usar **"Create a merge commit"**. **No** "Squash and merge" ni "Rebase and
  merge": como cada rama trae las anteriores, al aplastar commits el PR
  siguiente da conflicto.

---

## Si algo sale mal

- **El cherry-pick da conflicto:** casi siempre es porque partiste de la rama
  equivocada o el anterior todavía no hizo su push. Cancelá con
  `git cherry-pick --abort`, hacé `git fetch origin` y repetí desde
  `git checkout -B ...`.
- **`git push` pide permiso o falla:** tenés que ser colaborador del repo del
  profe; pedíselo.
- **Plan B:** en la carpeta `patches/` de esta rama están los mismos cambios
  como archivos `.patch`. En vez del `cherry-pick` se puede hacer
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
