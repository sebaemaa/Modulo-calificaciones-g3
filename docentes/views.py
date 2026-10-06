from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Docente, Materia, HorarioBloque, DIAS
from .forms import DocenteForm, MateriaForm, HorarioBloqueForm
from alumnos.models import Curso


# ================= DOCENTES =================

def index(request):
    docentes = Docente.objects.all()
    materias = Materia.objects.all()

    context = {
        'total_docentes': docentes.count(),
        'docentes_activos': docentes.filter(activo=True).count(),
        'total_materias': materias.count(),
        'docentes': docentes,
    }
    return render(request, 'docentes/index.html', context)


def nuevo_docente(request):
    if request.method == 'POST':
        form = DocenteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Docente creado correctamente.')
            return redirect('docentes:index')
    else:
        form = DocenteForm()
    return render(request, 'docentes/form_docente.html', {'form': form, 'modo': 'nuevo'})


def editar_docente(request, pk):
    docente = get_object_or_404(Docente, pk=pk)
    if request.method == 'POST':
        form = DocenteForm(request.POST, instance=docente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Docente actualizado correctamente.')
            return redirect('docentes:index')
    else:
        form = DocenteForm(instance=docente)
    return render(request, 'docentes/form_docente.html', {'form': form, 'modo': 'editar', 'docente': docente})


def detalle_docente(request, pk):
    docente = get_object_or_404(Docente, pk=pk)
    materias = docente.materias.all()
    return render(request, 'docentes/detalle_docente.html', {'docente': docente, 'materias': materias})


def baja_docente(request, pk):
    docente = get_object_or_404(Docente, pk=pk)
    if request.method == 'POST':
        docente.activo = not docente.activo
        docente.save()
        if docente.activo:
            messages.success(request, f'{docente} fue reactivado.')
        else:
            messages.warning(request, f'{docente} fue dado de baja.')
        return redirect('docentes:index')
    return render(request, 'docentes/confirmar_baja.html', {'docente': docente})


# ================= MATERIAS =================

def materias_list(request):
    materias = Materia.objects.select_related('curso', 'docente').all()
    return render(request, 'docentes/materias_list.html', {'materias': materias})


def nueva_materia(request):
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia creada correctamente.')
            return redirect('docentes:materias_list')
    else:
        form = MateriaForm()
    return render(request, 'docentes/form_materia.html', {'form': form, 'modo': 'nueva'})


def editar_materia(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia actualizada correctamente.')
            return redirect('docentes:materias_list')
    else:
        form = MateriaForm(instance=materia)
    return render(request, 'docentes/form_materia.html', {'form': form, 'modo': 'editar', 'materia': materia})


# ================= HORARIOS =================

def horarios_index(request):
    cursos = Curso.objects.all()
    return render(request, 'docentes/horarios_index.html', {'cursos': cursos})


def horario_curso(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    bloques = (HorarioBloque.objects
               .filter(materia__curso=curso)
               .select_related('materia', 'materia__docente')
               .order_by('dia', 'hora_inicio'))

    por_dia = {codigo: [] for codigo, _ in DIAS}
    for bloque in bloques:
        por_dia[bloque.dia].append(bloque)

    filas = [(codigo, nombre, por_dia[codigo]) for codigo, nombre in DIAS]

    return render(request, 'docentes/horario_curso.html', {'curso': curso, 'filas': filas})


def nuevo_horario(request):
    if request.method == 'POST':
        form = HorarioBloqueForm(request.POST)
        if form.is_valid():
            bloque = form.save()
            messages.success(request, 'Horario cargado correctamente.')
            return redirect('docentes:horario_curso', curso_id=bloque.materia.curso.id)
    else:
        form = HorarioBloqueForm()
    return render(request, 'docentes/form_horario.html', {'form': form})