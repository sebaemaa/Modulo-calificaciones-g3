# Cómo contribuir al proyecto

## Primera vez: clonar el repositorio

```bash
git clone https://github.com/sebaemaa/Modulo-calificaciones-g3.git
cd Modulo-calificaciones-g3
```

Verificá que tenés tu rama:

```bash
git branch -a
```

Deberías ver `feat/kenai`, `feat/lera` o `feat/lautaro` (la tuya).

## Pararte en tu rama

```bash
git checkout feat/tu-rama
```

Reemplazá `feat/tu-rama` por la tuya (`feat/kenai`, `feat/lera` o `feat/lautaro`).

## Trabajar en los cambios

1. Hacé tus modificaciones en el código
2. Agregá los archivos modificados:

```bash
git add .
```

3. Hacé un commit con un mensaje descriptivo:

```bash
git commit -m "Descripción corta de lo que hiciste"
```

4. Subí tus cambios a GitHub:

```bash
git push origin feat/tu-rama
```

## Crear un Pull Request (PR)

Cuando termines una funcionalidad o arreglo:

1. Andá a: **https://github.com/sebaemaa/Modulo-calificaciones-g3/pulls**
2. Hacé clic en **"New pull request"**
3. Seleccioná:
   - **base:** `dev`
   - **compare:** `feat/tu-rama`
4. Ponele un título claro y describí los cambios
5. Hacé clic en **"Create pull request"**
6. Avisá al líder para que revise y mergee

## Mantener tu rama actualizada

Si pasa el tiempo y tu rama quedó atrás respecto a `dev`:

```bash
git checkout dev
git pull origin dev
git checkout feat/tu-rama
git merge dev
# resolvé conflictos si los hay
git push origin feat/tu-rama
```

## Reglas importantes

- ✅ Trabajá **siempre** en tu rama (`feat/tu-rama`)
- ✅ Hacé commits chicos y frecuentes
- ✅ Commiteá **antes** de hacer `git pull` o cambiar de rama
- ❌ **Nunca** hagas push directo a `main` o `dev`
- ❌ **Nunca** toques módulos que no son tuyos
- ❌ **Nunca** uses `--force` a menos que sepas exactamente lo que hacés

## ¿Problemas?

Si algo no funciona, preguntale al líder del grupo antes de intentar soluciones complicadas.
