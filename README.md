# Módulo 3 (Calificaciones): cómo sube cada uno su parte

El módulo está terminado y dividido en **4 partes**, una por integrante. Cada
parte ya está en su rama del **repo del grupo**:
`https://github.com/sebaemaa/Modulo-calificaciones-g3`

Cada uno la lleva **desde su máquina** al **repo del profe**
(`https://github.com/eest3-hurlingham/sge-modulo3`), a su rama, y abre un Pull
Request hacia `dev`. Así el commit queda **a tu nombre**.

| Orden | Quién | Rama | Qué trae |
|---|---|---|---|
| 1 | Seba | `seba` | Modelos y migraciones, diseño del módulo, menú según el rol y boletín completo (publicación anual, RITE, firmas y permisos) |
| 2 | Lautaro | `lautaro` | Cargar notas (guardado automático), categorías de evaluación e importación de Excel |
| 3 | Axel | `lerafer` | Planilla de calificaciones (hoja oficial): cierre y reapertura del cuatrimestre, intensificación y nota final |
| 4 | Kenai | `kenai` | Tests y comando de datos de demostración |

Las partes solo tocan archivos del módulo (`calificaciones/`,
`templates/calificaciones/` y `static/css/calificaciones.css`). No modifican
nada de los otros grupos.

> ## ⚠ El orden importa
> Cada parte usa código de la anterior. **No subas la tuya hasta que el PR
> del anterior esté mergeado en `dev`** del repo del profe:
>
> **Seba → Lautaro → Axel → Kenai**
>
> Cuando te mergeen, avisale al siguiente por el grupo.

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

## Los pasos (iguales para todos, cambia solo el nombre de la rama)

Reemplazá `<rama>` por la tuya: `seba`, `lautaro`, `lerafer` o `kenai`.

```bash
# 1. Traer lo último de los dos repos
git fetch origin
git fetch grupo

# 2. Partir del dev del profe (que ya tiene las partes anteriores)
git checkout dev
git pull origin dev

# 3. Rehacer tu rama desde ahí (la rama ya existe con código viejo)
git checkout -B <rama>

# 4. Traer SOLO tu parte desde el repo del grupo
git cherry-pick --no-commit grupo/<rama>

# 5. Commit con tu usuario
git commit -m "<tu mensaje, ver abajo>"

# 6. Subir a tu rama del repo del profe
git push --force origin <rama>
```

**7.** En GitHub, en el repo del profe, abrí un **Pull Request** de `<rama>`
hacia **`dev`** y avisá en el grupo.

---

## Qué hace cada uno

### 1. Seba (`seba`), empieza primero
```bash
git checkout -B seba
git cherry-pick --no-commit grupo/seba
git commit -m "feat(calificaciones): base del modulo, menu por rol y boletin RITE"
git push --force origin seba
```
PR `seba` → `dev`. Cuando lo mergeen, le avisa a Lautaro.

### 2. Lautaro (`lautaro`), cuando esté mergeada la de Seba
```bash
git checkout -B lautaro
git cherry-pick --no-commit grupo/lautaro
git commit -m "feat(calificaciones): carga de notas, categorias e importacion de Excel"
git push --force origin lautaro
```
PR `lautaro` → `dev`. Cuando lo mergeen, le avisa a Axel.

### 3. Axel (`lerafer`), cuando esté mergeada la de Lautaro
```bash
git checkout -B lerafer
git cherry-pick --no-commit grupo/lerafer
git commit -m "feat(calificaciones): planilla de calificaciones, cierre e intensificacion"
git push --force origin lerafer
```
PR `lerafer` → `dev`. Cuando lo mergeen, le avisa a Kenai.

### 4. Kenai (`kenai`), cuando esté mergeada la de Axel
```bash
git checkout -B kenai
git cherry-pick --no-commit grupo/kenai
git commit -m "feat(calificaciones): tests y datos de demostracion"
git push --force origin kenai
```
PR `kenai` → `dev`. Con esta el módulo queda completo.

> Antes de cada `git checkout -B` acordate de hacer los pasos 1 y 2
> (`fetch` y `git checkout dev && git pull origin dev`).

---

## Si algo sale mal

- **El cherry-pick da conflicto:** casi siempre es porque `dev` todavía no
  tiene la parte anterior. Cancelá con `git cherry-pick --abort`, fijate que el
  PR anterior esté mergeado y repetí desde el paso 1.
- **`git push` pide permiso o falla:** tenés que ser colaborador del repo del
  profe; pedíselo.
- **Plan B:** en la carpeta `patches/` de esta rama están los mismos cambios
  como archivos `.patch`. En vez del paso 4 se puede hacer
  `git apply parte-N-<nombre>.patch` (con el archivo copiado en la carpeta del
  repo) y después `git add -A`.

---

## Probar que anda (después de la parte 4)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_datos_demo
python manage.py test calificaciones     # tienen que dar OK
python manage.py runserver
```

Usuarios de prueba (clave `prueba1234`): `profesor1` y `profesor2` (docentes),
`preceptora` (secretaría) y `acosta.lucia` (alumna). Para importar o descargar
Excel hace falta `pip install openpyxl`.
