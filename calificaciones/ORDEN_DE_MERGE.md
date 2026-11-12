# Módulo 3 (Calificaciones): orden de merge

El módulo está dividido en **4 features**, una por integrante del Grupo 3.
Cada rama está armada **encima de la anterior**, así que los Pull Requests
hacia `dev` se mergean **en este orden**:

| Orden | Rama | Integrante | Feature |
|---|---|---|---|
| 1 | `seba` | Seba | Modelos y migraciones, diseño del módulo, menú según el rol y boletín (publicación anual, RITE, firmas y permisos) |
| 2 | `lautaro` | Lautaro | Cargar notas (guardado automático), categorías de evaluación e importación de Excel |
| 3 | `lerafer` | Axel | Planilla de calificaciones: cierre y reapertura del cuatrimestre, intensificación y nota final |
| 4 | `kenai` | Kenai | Tests y comando de datos de demostración |

> **⚠ Importante: mergear con "Create a merge commit".**
> No usar "Squash and merge" ni "Rebase and merge": como cada rama trae las
> anteriores, al aplastar los commits el PR siguiente da conflicto.

Notas para el merge:

- Mientras no se mergea el PR anterior, cada PR muestra también los cambios de
  los anteriores. Después de mergear uno, el siguiente muestra solo su feature.
- "Create a merge commit" además conserva el commit de cada integrante.
- Las 4 features solo modifican archivos del módulo (`calificaciones/`,
  `templates/calificaciones/` y `static/css/calificaciones.css`).
- Después de mergear las 4:
  `python manage.py migrate` y `python manage.py test calificaciones`.
