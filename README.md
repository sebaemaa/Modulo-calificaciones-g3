# SGE — Sistema de Gestión Escolar
**EEST N°3 Hurlingham — 7° Año Programación 2026 — Módulo Calificaciones**

![Python](https://img.shields.io/badge/Python-3-blue)
![Django](https://img.shields.io/badge/Django-6-green)
![License](https://img.shields.io/badge/license-MIT-green)
![GitHub contributors](https://img.shields.io/github/contributors/sebaemaa/Modulo-calificaciones-g3)

## Stack tecnológico
- Python 3 + Django 6
- ORM nativo de Django
- Base de datos: SQLite (compartida)
- Frontend: Bootstrap 5
- Control de versiones: Git + GitHub

## Módulos

| Módulo | URL base | Responsable |
|--------|----------|-------------|
| Gestión de Alumnos | `/alumnos/` | Grupo 1 |
| Gestión de Asistencia | `/asistencia/` | Grupo 2 |
| Gestión de Calificaciones | `/calificaciones/` | **Grupo 3 — nuestro equipo** |
| Gestión de Docentes y Materias | `/docentes/` | Grupo 4 |
| Comunicados y Notificaciones | `/comunicados/` | Grupo 5 |

## Nuestro equipo — Grupo 3 (Calificaciones)

| Integrante | GitHub | Rama |
|------------|--------|------|
| Sebastián (líder) | [sebaemaa](https://github.com/sebaemaa) | `main` |
| Kenai Luque | [kenailuque](https://github.com/kenailuque) | `feat/kenai` |
| Lera Fer | [lerafer](https://github.com/lerafer) | `feat/lera` |
| Lautaro Ba | [lautaroba2025-netizen](https://github.com/lautaroba2025-netizen) | `feat/lautaro` |

## Cómo contribuir (para el grupo)

Mirá la **[GUÍA COMPLETA → CONTRIBUTING.md](CONTRIBUTING.md)**. En resumen:

1. Cada integrante trabaja en **su propia rama** (`feat/kenai`, `feat/lera`, `feat/lautaro`)
2. Los cambios se integran mediante **Pull Requests** hacia `dev`
3. El líder revisa y mergea los PRs
4. Periódicamente se actualiza `main` desde `dev`

## Cómo correr el proyecto localmente

### Primera vez

```bash
# 1. Clonar el repositorio (si no lo tenés)
git clone https://github.com/sebaemaa/Modulo-calificaciones-g3.git
cd Modulo-calificaciones-g3

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar el entorno virtual
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Crear la base de datos
python manage.py migrate

# 6. Iniciar el servidor
python manage.py runserver
```

Abrí el navegador en: **http://127.0.0.1:8000**

### Cada vez que trabajás

```bash
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux
python manage.py runserver
```

## Estructura del proyecto

```
sge/
├── sge/                    ← configuración principal (solo el profe)
│   ├── settings.py
│   └── urls.py
├── core/                   ← página de inicio (solo el profe)
├── alumnos/                ← Módulo 1
│   ├── models.py           ← modelos de la base de datos
│   ├── views.py            ← lógica de las vistas
│   └── urls.py             ← rutas del módulo
├── asistencia/             ← Módulo 2
├── calificaciones/         ← Módulo 3
├── docentes/               ← Módulo 4
├── comunicados/            ← Módulo 5
├── templates/
│   ├── base.html           ← template base (solo el profe)
│   ├── alumnos/            ← templates del Módulo 1
│   ├── asistencia/         ← templates del Módulo 2
│   ├── calificaciones/     ← templates del Módulo 3
│   ├── docentes/           ← templates del Módulo 4
│   └── comunicados/        ← templates del Módulo 5
├── static/
│   ├── css/base.css
│   └── js/base.js
├── requirements.txt
├── .gitignore
└── manage.py
```

## Reglas del proyecto

- Cada grupo edita **solo su módulo** (`models.py`, `views.py`, `urls.py`, templates)
- **No tocar** `base.html`, `settings.py`, `urls.py` principal ni módulos ajenos
- Para consultar datos de otro módulo: importar su modelo, no duplicar tablas
- **Nunca hacer push directo a `dev` ni a `main`** — trabajar en la rama del grupo
- Commits frecuentes con mensajes descriptivos
- Ante dudas sobre la estructura compartida: consultá al profe antes de tocar algo
