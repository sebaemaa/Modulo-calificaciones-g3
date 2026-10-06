// JavaScript exclusivo del módulo de alumnos.

const REQUIRED_DOCS = [
  {
    key: 'identidad',
    label: 'Documento de identidad / CUIL',
    patterns: ['dni', 'documento', 'cuil'],
  },
  {
    key: 'partida',
    label: 'Partida de nacimiento',
    patterns: ['partida', 'nacimiento'],
  },
  {
    key: 'vacunas',
    label: 'Certificado de vacunas',
    patterns: ['vacuna', 'vacunas', 'sanitario', 'salud'],
  },
  {
    key: 'constancia',
    label: 'Constancia / ficha medica',
    patterns: ['constancia', 'regular', 'ficha', 'medica', 'médica'],
  },
];

let __documentosExistentesEditar = [];
let __documentosCompletosEditarKeys = [];

document.addEventListener('DOMContentLoaded', function () { 
  const formAlumno = document.getElementById('formAlumno');
  const openFormButton = document.querySelector('.js-open-form');
  const closeFormButton = document.querySelector('.js-close-form');
  const btnPromocionarCurso = document.getElementById('btnPromocionarCurso');
  const btnCargarPromocionCurso = document.getElementById('btnCargarPromocionCurso');
  const btnConfirmarPromocionCurso = document.getElementById('btnConfirmarPromocionCurso');
  const btnSeleccionarAptosPromocion = document.getElementById('btnSeleccionarAptosPromocion');
  const btnLimpiarSeleccionPromocion = document.getElementById('btnLimpiarSeleccionPromocion');
/* Espera que cargue la página y obtiene el formulario y los botones de abrir/cerrar.*/
  if (openFormButton && formAlumno) {
    openFormButton.addEventListener('click', function () {
      formAlumno.classList.remove('is-hidden');
    });
  } /*// Si existe el botón y el formulario,
// al hacer click muestra el formulario.*/

  if (closeFormButton && formAlumno) {
    closeFormButton.addEventListener('click', function () {
      formAlumno.classList.add('is-hidden');
    });
  }/*// Oculta el formulario al presionar cerrar.*/

  document.querySelectorAll('.js-doc-tooltip').forEach(function (element) {
    if (window.bootstrap && bootstrap.Tooltip) {
      new bootstrap.Tooltip(element, {
        placement: 'top',
        trigger: 'hover focus',
      });
    }
  });

   // ==============================
// Buscador de archivos
// ==============================
document.querySelectorAll('.doc-search-input').forEach(function (input) {

  input.addEventListener('input', function () {

    const texto = this.value.trim().toLowerCase();

    // Tomamos el contenedor correcto del modal de archivos.
    // Esto evita que el filtrado se aplique al modal equivocado.
    const modal = (this.closest && (this.closest('[id^="modalArchivos-"]') || this.closest('.modal')))
      ? (this.closest('[id^="modalArchivos-"]') || this.closest('.modal'))
      : null;

    if (!modal) return;



    const items = modal.querySelectorAll('.doc-item');

    items.forEach(function (item) {
      const nombre = (item.dataset.search || '').toLowerCase();
      item.style.display = (texto === '' || nombre.includes(texto)) ? '' : 'none';
    });

    // Mostrar u ocultar grupos según tengan resultados
    modal.querySelectorAll('.doc-day-group').forEach(function (grupo) {
      const hayVisibles = Array.from(grupo.querySelectorAll('.doc-item'))
        .some(function (item) {
          return item.style.display !== 'none';
        });

      grupo.style.display = hayVisibles ? '' : 'none';
    });

    // Si todo quedó oculto, mostramos un mensaje único dentro del modal.
    const cualquierDocumentoVisible = Array.from(modal.querySelectorAll('.doc-item'))
      .some(function (item) { return item.style.display !== 'none'; });

    let noResults = modal.querySelector('.doc-no-results');
    if (!cualquierDocumentoVisible) {
      if (!noResults) {
        noResults = document.createElement('div');
        noResults.className = 'doc-no-results no-results';
        noResults.textContent = 'No se encontraron archivos con ese texto.';
        modal.querySelector('.doc-modal-list').appendChild(noResults);
      }
    } else if (noResults) {
      noResults.remove();
    }



  });

});


  flatpickr("#e-fecha, #n-fecha, #baja-fecha, #expediente-fecha-emision", {
    dateFormat: "Y-m-d",
    allowInput: true
  });

  const hoy = new Date();
  const y = hoy.getFullYear();
  const m = String(hoy.getMonth() + 1).padStart(2, '0');
  const d = String(hoy.getDate()).padStart(2, '0');
  const bajaFecha = document.getElementById('baja-fecha');
  if (bajaFecha && !bajaFecha.value) {
    setDateControlValue('baja-fecha', `${y}-${m}-${d}`);
  }

  const nFecha = document.getElementById('n-fecha');
  const eFecha = document.getElementById('e-fecha');
  const nTipo = document.getElementById('n-tipo-identificacion');
  const eTipo = document.getElementById('e-tipo-identificacion');
  if (nFecha) nFecha.addEventListener('input', actualizarEdadNuevoAlumno);
  if (eFecha) eFecha.addEventListener('input', actualizarEdadEditarAlumno);
  if (nTipo) nTipo.addEventListener('change', () => actualizarLabelIdentificacion('n'));
  if (eTipo) eTipo.addEventListener('change', () => actualizarLabelIdentificacion('e'));

  actualizarEdadNuevoAlumno();
  actualizarEdadEditarAlumno();
  actualizarLabelIdentificacion('n');
  actualizarLabelIdentificacion('e');

  bindDocumentacionChecklistNuevo();
  bindDocumentacionChecklistEditar();

  if (btnPromocionarCurso) {
    btnPromocionarCurso.addEventListener('click', function () {
      const filtroAnio = document.getElementById('filtro-anio');
      const filtroDivision = document.getElementById('filtro-division');
      const anioInput = document.getElementById('promocion-anio');
      const divisionInput = document.getElementById('promocion-division');
      if (anioInput && filtroAnio && filtroAnio.value) anioInput.value = filtroAnio.value;
      if (divisionInput && filtroDivision && filtroDivision.value) divisionInput.value = filtroDivision.value;
      new bootstrap.Modal(document.getElementById('modalPromocionCurso')).show();
    });
  }

  if (btnCargarPromocionCurso) {
    btnCargarPromocionCurso.addEventListener('click', cargarPromocionCurso);
  }

  if (btnConfirmarPromocionCurso) {
    btnConfirmarPromocionCurso.addEventListener('click', confirmarPromocionCurso);
  }

  if (btnSeleccionarAptosPromocion) {
    btnSeleccionarAptosPromocion.addEventListener('click', seleccionarTodosAptosPromocion);
  }

  if (btnLimpiarSeleccionPromocion) {
    btnLimpiarSeleccionPromocion.addEventListener('click', limpiarSeleccionPromocion);
  }

  // Mantiene la edad visible al día sin recargar página.
  setInterval(() => {
    actualizarEdadNuevoAlumno();
    actualizarEdadEditarAlumno();
    const vFechaEl = document.getElementById('v-fecha');
    const vEdadEl = document.getElementById('v-edad');
    if (vFechaEl && vEdadEl) {
      const edadFicha = calcularEdad(vFechaEl.textContent || '');
      if (edadFicha !== null) vEdadEl.textContent = `${edadFicha} años`;
    }
  }, 60 * 60 * 1000);
}); /*// Aplica el calendario a los campos de fecha
// y muestra/guarda la fecha en formato Año-Mes-Día.*/

function getCsrfToken() {
  const cookieMatch = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
  if (cookieMatch && cookieMatch[1]) {
    return decodeURIComponent(cookieMatch[1]);
  }

  const node = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return node ? node.value : '';
}

function clearPromocionFeedback() {
  const feedback = document.getElementById('promocionFeedback');
  if (!feedback) return;
  feedback.className = 'promo-feedback';
  feedback.textContent = '';
}

function setPromocionFeedback(message, type = 'error') {
  const feedback = document.getElementById('promocionFeedback');
  if (!feedback) return;
  feedback.className = `promo-feedback is-visible ${type === 'success' ? 'is-success' : 'is-error'}`;
  feedback.innerHTML = message;
}

let __promocionCursoItems = [];

const MOTIVOS_NO_PROMOCION = [
  { value: '', label: 'Seleccionar motivo' },
  { value: 'Materias pendientes', label: 'Materias pendientes' },
  { value: 'Inasistencias', label: 'Inasistencias' },
  { value: 'Abandono', label: 'Abandono' },
  { value: 'Cambio de institucion', label: 'Cambio de institucion' },
  { value: 'Otro', label: 'Otro' },
];

function buildMotivoSelect(selected = '') {
  return `
    <select class="form-select js-motivo-no-promocion" title="Motivo de no promocion" aria-label="Motivo de no promocion">
      ${MOTIVOS_NO_PROMOCION.map((opt) => `<option value="${escapeHtml(opt.value)}" ${selected === opt.value ? 'selected' : ''}>${escapeHtml(opt.label)}</option>`).join('')}
    </select>
  `;
}

function buildDestinoModeSelect() {
  return `
    <select class="form-select js-destino-mode" title="Destino del alumno promocionado" aria-label="Destino del alumno promocionado">
      <option value="misma">Siguiente año, misma división</option>
      <option value="cambiar">Siguiente año, cambiar división</option>
    </select>
  `;
}

function buildDestinoDivisionSelect(selected = '') {
  const divisiones = ['A', 'B', 'C', 'D'];
  return `
    <select class="form-select js-destino-division" title="Nueva división" aria-label="Nueva división" disabled>
      ${divisiones.map((d) => `<option value="${d}" ${selected === d ? 'selected' : ''}>${d}</option>`).join('')}
    </select>
  `;
}

function toggleDestinationInputs(tr) {
  const chk = tr.querySelector('.js-promocionar-check');
  const mode = tr.querySelector('.js-destino-mode');
  const division = tr.querySelector('.js-destino-division');

  if (!mode || !division) return;

  const selected = !!(chk && chk.checked && !chk.disabled);
  const cambiar = mode.value === 'cambiar';

  mode.disabled = !selected;
  division.disabled = !selected || !cambiar;
}

function toggleReasonInputs(tr) {
  const chk = tr.querySelector('.js-promocionar-check');
  const select = tr.querySelector('.js-motivo-no-promocion');
  const inputOtro = tr.querySelector('.js-motivo-otro');
  const isSelected = !!(chk && chk.checked && !chk.disabled);

  tr.classList.toggle('promo-row-selected', isSelected);

  if (select) select.disabled = isSelected;
  if (inputOtro) {
    const selectedMotivo = select ? select.value : '';
    const isOtro = selectedMotivo === 'Otro';
    inputOtro.disabled = isSelected || !isOtro;
    inputOtro.required = !isSelected && isOtro;
    if (!isOtro) inputOtro.value = '';
  }

  toggleDestinationInputs(tr);
}

function updatePromocionResumenUI() {
  const rows = Array.from(document.querySelectorAll('#tablaPromocionCurso tbody tr[data-alumno-id]'));
  let promovidos = 0;
  const noProm = [];

  rows.forEach((tr) => {
    const chk = tr.querySelector('.js-promocionar-check');
    const select = tr.querySelector('.js-motivo-no-promocion');
    const inputOtro = tr.querySelector('.js-motivo-otro');
    const nombre = tr.dataset.alumnoNombre || 'Alumno';
    const selected = !!(chk && chk.checked && !chk.disabled);

    if (selected) {
      promovidos += 1;
      return;
    }

    const motivoBase = select ? select.value : '';
    const motivo = motivoBase === 'Otro' ? (inputOtro?.value || '').trim() : motivoBase;
    noProm.push({ nombre, motivo: motivo || '(sin motivo)' });
  });

  const resumenProm = document.getElementById('resumenPromocionCount');
  const resumenNoProm = document.getElementById('resumenNoPromocionCount');
  const listado = document.getElementById('resumenNoPromocionListado');

  if (resumenProm) resumenProm.textContent = `Promocionados: ${promovidos}`;
  if (resumenNoProm) resumenNoProm.textContent = `No promocionados: ${noProm.length}`;
  if (listado) {
    if (!noProm.length) {
      listado.textContent = 'Todos los alumnos seleccionados para promocion.';
    } else {
      listado.innerHTML = noProm
        .map((item) => `<div><b>${escapeHtml(item.nombre)}:</b> ${escapeHtml(item.motivo)}</div>`)
        .join('');
    }
  }
}

function bindPromocionRowEvents() {
  document.querySelectorAll('#tablaPromocionCurso tbody tr[data-alumno-id]').forEach((tr) => {
    const chk = tr.querySelector('.js-promocionar-check');
    const select = tr.querySelector('.js-motivo-no-promocion');
    const inputOtro = tr.querySelector('.js-motivo-otro');
    const destinoMode = tr.querySelector('.js-destino-mode');
    const destinoDivision = tr.querySelector('.js-destino-division');

    if (chk) chk.addEventListener('change', () => {
      toggleReasonInputs(tr);
      updatePromocionResumenUI();
    });
    if (select) select.addEventListener('change', () => {
      toggleReasonInputs(tr);
      updatePromocionResumenUI();
    });
    if (inputOtro) inputOtro.addEventListener('input', updatePromocionResumenUI);
    if (destinoMode) destinoMode.addEventListener('change', () => {
      toggleDestinationInputs(tr);
      updatePromocionResumenUI();
    });
    if (destinoDivision) destinoDivision.addEventListener('change', updatePromocionResumenUI);

    toggleReasonInputs(tr);
  });

  updatePromocionResumenUI();
}

function seleccionarTodosAptosPromocion() {
  const rows = Array.from(document.querySelectorAll('#tablaPromocionCurso tbody tr[data-alumno-id]'));
  rows.forEach((tr) => {
    const chk = tr.querySelector('.js-promocionar-check');
    if (!chk || chk.disabled) return;

    const aptoBadge = tr.querySelector('.badge-activo');
    chk.checked = !!aptoBadge;
    toggleReasonInputs(tr);
  });

  updatePromocionResumenUI();
}

function limpiarSeleccionPromocion() {
  const rows = Array.from(document.querySelectorAll('#tablaPromocionCurso tbody tr[data-alumno-id]'));
  rows.forEach((tr) => {
    const chk = tr.querySelector('.js-promocionar-check');
    if (!chk || chk.disabled) return;

    chk.checked = false;
    toggleReasonInputs(tr);
  });

  updatePromocionResumenUI();
}

async function cargarPromocionCurso() {
  const anio = document.getElementById('promocion-anio')?.value || '';
  const division = document.getElementById('promocion-division')?.value || '';
  const tbody = document.querySelector('#tablaPromocionCurso tbody');
  const resumen = document.getElementById('promocionCursoResumen');
  clearPromocionFeedback();

  if (!anio || !division) {
    if (tbody) tbody.innerHTML = '<tr><td colspan="8" class="no-results">Selecciona anio y division.</td></tr>';
    return;
  }

  if (tbody) tbody.innerHTML = '<tr><td colspan="8" class="no-results">Evaluando alumnos...</td></tr>';

  const res = await fetch(`/alumnos/promocion-curso/resumen/?anio=${encodeURIComponent(anio)}&division=${encodeURIComponent(division)}`);
  const payload = await res.json();
  const items = payload.items || [];
  __promocionCursoItems = items;

  if (!items.length) {
    if (tbody) tbody.innerHTML = '<tr><td colspan="8" class="no-results">No hay alumnos para ese curso/division.</td></tr>';
    if (resumen) resumen.textContent = '';
    updatePromocionResumenUI();
    return;
  }

  if (tbody) {
    tbody.innerHTML = items.map((item) => {
      const motivoSugerido = item.puede_promocionar ? '' : (item.motivo || 'No cumple requisitos');
      const checkedDefault = item.puede_promocionar;
      const disabledCheck = !Boolean(item.activo) || String(item.curso) === '7';

      return `
        <tr data-alumno-id="${item.id}" data-alumno-nombre="${escapeHtml((item.apellido || '') + ', ' + (item.nombre || ''))}" class="${checkedDefault ? 'promo-row-selected' : ''} ${disabledCheck ? 'promo-row-disabled' : ''}">
          <td data-label="Nombre y apellido">${escapeHtml(item.apellido || '')}, ${escapeHtml(item.nombre || '')}</td>
          <td class="promo-dni-cell" data-label="DNI">${escapeHtml(item.dni || '')}</td>
          <td data-label="Curso">${escapeHtml(String(item.curso || '-'))}°</td>
          <td data-label="División">${escapeHtml(item.division || '-')}</td>
          <td data-label="Estado actual">${escapeHtml(item.estado || '-')}</td>
          <td class="promo-select-cell" data-label="Promocionar">
            <div class="form-check form-switch">
              <input class="form-check-input js-promocionar-check" type="checkbox" ${checkedDefault ? 'checked' : ''} ${disabledCheck ? 'disabled' : ''}>
              <label class="form-check-label">Promocionar</label>
            </div>
          </td>
          <td class="promo-destino-cell" data-label="Destino">
            <div class="promo-destino-wrap">
              ${buildDestinoModeSelect()}
              ${buildDestinoDivisionSelect(item.division || 'A')}
            </div>
          </td>
          <td class="promo-reason-cell" data-label="Motivo no promoción">
            <div class="promo-reason-wrap">
              ${buildMotivoSelect(motivoSugerido)}
              <input type="text" class="form-control js-motivo-otro" placeholder="Detalle de otro motivo" disabled>
            </div>
          </td>
        </tr>
      `;
    }).join('');
    bindPromocionRowEvents();
  }

  const aptos = items.filter((x) => x.puede_promocionar).length;
  if (resumen) resumen.textContent = `${aptos} aptos sugeridos de ${items.length} alumnos`;
}

async function confirmarPromocionCurso() {
  const anio = document.getElementById('promocion-anio')?.value || '';
  const division = document.getElementById('promocion-division')?.value || '';
  clearPromocionFeedback();
  if (!anio || !division) {
    setPromocionFeedback('Seleccioná año y división para continuar.');
    return;
  }

  const rows = Array.from(document.querySelectorAll('#tablaPromocionCurso tbody tr[data-alumno-id]'));
  if (!rows.length) {
    setPromocionFeedback('Primero cargá el curso y la división a promocionar.');
    return;
  }

  const decisiones = [];
  const faltantes = [];

  rows.forEach((tr) => {
    const alumnoId = Number(tr.dataset.alumnoId || 0);
    const alumnoNombre = tr.dataset.alumnoNombre || 'Alumno';
    const chk = tr.querySelector('.js-promocionar-check');
    const select = tr.querySelector('.js-motivo-no-promocion');
    const inputOtro = tr.querySelector('.js-motivo-otro');
    const destinoMode = tr.querySelector('.js-destino-mode');
    const destinoDivision = tr.querySelector('.js-destino-division');
    const bloqueado = !!(chk && chk.disabled);

    const promover = !!(chk && chk.checked && !bloqueado);
    const motivoBase = select ? select.value : '';
    const motivo = motivoBase === 'Otro' ? (inputOtro?.value || '').trim() : motivoBase;

    if (!promover && !bloqueado && !motivo) {
      faltantes.push(alumnoNombre);
    }

    decisiones.push({
      alumno_id: alumnoId,
      promover,
      motivo_no_promocion: promover ? '' : motivo,
      destino_mode: promover ? (destinoMode?.value || 'misma') : 'misma',
      destino_division: promover ? (destinoDivision?.value || '') : '',
    });
  });

  if (faltantes.length) {
    setPromocionFeedback(`Falta completar motivo en: <b>${faltantes.join(' | ')}</b>.`);
    return;
  }

  updatePromocionResumenUI();

  if (!confirm('Se validó el resumen. ¿Confirmar promoción definitiva?')) {
    return;
  }

  const res = await fetch('/alumnos/promocion-curso/confirmar/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({
      anio,
      division,
      decisiones,
    }),
  });

  const payload = await res.json();
  if (!payload.ok) {
    if (payload.faltantes && payload.faltantes.length) {
      setPromocionFeedback(`No se pudo confirmar. Faltan motivos en: <b>${payload.faltantes.join(' | ')}</b>.`);
    } else {
      setPromocionFeedback(payload.message || 'No se pudo confirmar la promoción.');
    }
    return;
  }

  const detalle = (payload.detalle_no_promovidos || [])
    .map((d) => `${d.alumno}: ${d.motivo}`)
    .join('<br>');
  setPromocionFeedback(
    `Promovidos: <b>${payload.promovidos}</b> | No promocionados: <b>${payload.no_promovidos}</b>${detalle ? `<br><br>Detalle no promocionados:<br>${detalle}` : ''}`,
    'success'
  );

  const modalEl = document.getElementById('modalPromocionCurso');
  const modalInst = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;
  if (modalInst) {
    modalInst.hide();
  }

  setTimeout(() => {
    window.location.reload();
  }, 220);
}

function actualizarLabelIdentificacion(prefix) {
  const select = document.getElementById(`${prefix}-tipo-identificacion`);
  const label = document.getElementById(`${prefix}-ident-label`);
  const input = document.getElementById(`${prefix}-ident-numero`) || document.getElementById(`${prefix}-dni`);
  if (!select || !label || !input) return;

  const isCuilProvisorio = select.value === 'cuil_provisorio';
  label.textContent = isCuilProvisorio ? 'CUIL provisorio' : 'Documento';
  input.placeholder = isCuilProvisorio ? 'Ingresar CUIL provisorio' : 'Ingresar DNI';
}

function calcularEdad(fechaNacimiento) {
  const normalized = normalizeDateForInput(fechaNacimiento);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(normalized)) return null;

  const [yy, mm, dd] = normalized.split('-').map((x) => parseInt(x, 10));
  const nacimiento = new Date(yy, mm - 1, dd);
  if (Number.isNaN(nacimiento.getTime())) return null;

  const hoy = new Date();
  let edad = hoy.getFullYear() - nacimiento.getFullYear();
  const mesDiff = hoy.getMonth() - nacimiento.getMonth();
  const diaDiff = hoy.getDate() - nacimiento.getDate();
  if (mesDiff < 0 || (mesDiff === 0 && diaDiff < 0)) {
    edad -= 1;
  }
  return edad >= 0 ? edad : null;
}

function actualizarEdadNuevoAlumno() {
  const fechaInput = document.getElementById('n-fecha');
  const target = document.getElementById('n-edad');
  if (!fechaInput || !target) return;
  const edad = calcularEdad(fechaInput.value);
  target.textContent = edad === null ? '-' : `${edad} años`;
}

function actualizarEdadEditarAlumno() {
  const fechaInput = document.getElementById('e-fecha');
  const target = document.getElementById('e-edad');
  if (!fechaInput || !target) return;
  const edad = calcularEdad(fechaInput.value);
  target.textContent = edad === null ? '-' : `${edad} años`;
}

function normalizeDateForInput(dateValue) {
  if (!dateValue) {
    return '';
  } /*Función que normaliza la fecha para el input.
    Si no hay fecha, devuelve vacío.*/

  const value = String(dateValue).trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
    return value.substring(0, 10);
  } /*Convierte la fecha a texto y quita espacios.
     Si ya está en formato Año-Mes-Día, devuelve solo esa parte.*/

  const parts = value.split('/');
  if (parts.length === 3) {
    const [day, month, year] = parts;
    return `${year.padStart(4, '0')}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  } /* Separa la fecha si viene con "/".
Si tiene día, mes y año, la convierte al formato Año-Mes-Día.*/

  return value.substring(0, 10);
} /* // Devuelve solo los primeros 10 caracteres de la fecha (YYYY-MM-DD).*/

function formatDateForDisplay(dateValue) {
  const normalized = normalizeDateForInput(dateValue);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    return dateValue || '';
  } /*Convierte la fecha al formato correcto para mostrar.
Si no tiene el formato Año-Mes-Día, devuelve la original.*/

  return normalized;
} /* // Devuelve la fecha ya normalizada en formato Año-Mes-Día.*/

function setDateControlValue(inputId, dateValue) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const normalized = normalizeDateForInput(dateValue);
  if (input._flatpickr) {
    input._flatpickr.setDate(normalized || null, true, 'Y-m-d');
    return;
  }

  input.value = normalized;
}

function evaluarDocumentacionRequerida(fileNames, explicitCompleteKeys) {
  const archivos = (fileNames || [])
    .map((name) => String(name || '').trim().toLowerCase())
    .filter(Boolean);
  const completosForzados = new Set(explicitCompleteKeys || []);

  return REQUIRED_DOCS.map((doc) => {
    const completo = completosForzados.has(doc.key) || archivos.some((archivo) => doc.patterns.some((pattern) => archivo.includes(pattern)));
    return {
      key: doc.key,
      label: doc.label,
      completo,
    };
  });
}

function actualizarEstadoDocumentacionRequerida(panelId, warningId, fileNames, explicitCompleteKeys) {
  const panel = document.getElementById(panelId);
  const warning = document.getElementById(warningId);
  if (!panel || !warning) return;

  const estado = evaluarDocumentacionRequerida(fileNames, explicitCompleteKeys);
  estado.forEach((item) => {
    const row = panel.querySelector(`[data-doc-key="${item.key}"]`);
    if (!row) return;
    row.classList.toggle('is-complete', item.completo);
    row.classList.toggle('is-missing', !item.completo);

    const status = row.querySelector('.js-doc-required-status');
    if (status) status.textContent = item.completo ? 'Completo' : 'Falta';
  });

  const faltantes = estado.filter((item) => !item.completo).map((item) => item.label);
  if (!faltantes.length) {
    warning.textContent = 'Documentacion completa';
    warning.classList.remove('badge-doc-missing');
    warning.classList.add('badge-doc-ok');
    return;
  }

  warning.textContent = `Falta: ${faltantes.join(', ')}`;
  warning.classList.remove('badge-doc-ok');
  warning.classList.add('badge-doc-missing');
}

function parseDocumentacionArchivos(rawValue) {
  if (!rawValue) return [];
  return String(rawValue)
    .split('||')
    .map((name) => name.trim())
    .filter(Boolean);
}

function parseDocumentacionKeys(rawValue) {
  if (!rawValue) return [];
  return String(rawValue)
    .split('||')
    .map((value) => value.trim())
    .filter(Boolean);
}

function getRequiredDocInputs(prefix) {
  return Array.from(document.querySelectorAll(`#${prefix}-docs-required .js-doc-required-input`));
}

function getRequiredDocSelections(prefix) {
  const inputs = getRequiredDocInputs(prefix);
  const fileNames = [];
  const completedKeys = [];

  inputs.forEach((input) => {
    const key = input.dataset.docKey;
    const file = input.files && input.files[0] ? input.files[0] : null;
    if (file) {
      fileNames.push(file.name || '');
      if (key) completedKeys.push(key);
    }
  });

  return { fileNames, completedKeys };
}

function clearRequiredDocSelections(prefix) {
  getRequiredDocInputs(prefix).forEach((input) => {
    input.value = '';
  });
}

function bindDocumentacionChecklistNuevo() {
  const inputs = getRequiredDocInputs('n');
  const extraInput = document.getElementById('n-documentacion-extra');
  if (!inputs.length) return;

  const refrescar = function () {
    const seleccion = getRequiredDocSelections('n');
    const extraFiles = extraInput ? Array.from(extraInput.files || []).map((file) => file.name || '') : [];
    actualizarEstadoDocumentacionRequerida(
      'n-docs-required',
      'n-docs-warning',
      seleccion.fileNames.concat(extraFiles),
      seleccion.completedKeys
    );
  };

  inputs.forEach((input) => input.addEventListener('change', refrescar));
  if (extraInput) extraInput.addEventListener('change', refrescar);
  refrescar();
}

function bindDocumentacionChecklistEditar() {
  const inputs = getRequiredDocInputs('e');
  const extraInput = document.getElementById('e-documentacion-extra');
  if (!inputs.length) return;

  const refrescar = function () {
    actualizarEstadoDocumentacionEditar();
  };

  inputs.forEach((input) => input.addEventListener('change', refrescar));
  if (extraInput) extraInput.addEventListener('change', refrescar);
  refrescar();
}

function actualizarEstadoDocumentacionEditar() {
  const extraInput = document.getElementById('e-documentacion-extra');
  const extraFiles = extraInput ? Array.from(extraInput.files || []).map((file) => file.name || '') : [];
  const seleccion = getRequiredDocSelections('e');
  const todos = __documentosExistentesEditar.concat(seleccion.fileNames, extraFiles);
  const completedKeys = Array.from(new Set(__documentosCompletosEditarKeys.concat(seleccion.completedKeys)));
  actualizarEstadoDocumentacionRequerida('e-docs-required', 'e-docs-warning', todos, completedKeys);
}

function getExpedienteEstadoBadge(estado) {
  if (estado === 'vigente') return '<span class="badge-activo">Vigente</span>';
  if (estado === 'vencido') return '<span class="badge-inactivo">Vencido</span>';
  return '<span class="badge-doc-missing">Pendiente de actualización</span>';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function prepararBotonesExpediente(alumnoId) {
  document.querySelectorAll('.js-open-expediente').forEach((button) => {
    button.dataset.alumnoId = alumnoId;
  });
}

function renderExpedienteDocumentos(containerId, alumnoId, documentos) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const items = documentos || [];
  if (!items.length) {
    container.innerHTML = '<div class="text-muted">No hay documentos cargados en el legajo.</div>';
    return;
  }

  container.innerHTML = items.map((doc) => `
    <div class="expediente-card">
      <div class="expediente-card-header">
        <div>
          <div class="expediente-card-title">${escapeHtml(doc.nombre_documento || 'Documento sin nombre')}</div>
          <div class="text-muted small">${escapeHtml(doc.tipo_documento_label || doc.tipo_documento || '-')}</div>
        </div>
        <div class="d-flex align-items-center gap-2 flex-wrap justify-content-end">
          ${getExpedienteEstadoBadge(doc.estado)}
          <button type="button" class="btn btn-sm btn-outline-primary js-edit-expediente" data-alumno-id="${alumnoId}" data-documento-id="${doc.id}" data-documento-nombre="${escapeHtml(doc.nombre_documento || '')}" data-documento-tipo="${escapeHtml(doc.tipo_documento || '')}" data-documento-fecha-emision="${escapeHtml(doc.fecha_emision || '')}" data-documento-estado="${escapeHtml(doc.estado || 'vigente')}" data-documento-observaciones="${escapeHtml(doc.observaciones || '')}">Editar</button>
          ${doc.archivo_url ? `<a class="btn btn-sm btn-outline-secondary" href="${doc.archivo_url}" target="_blank" rel="noopener">Ver archivo</a>` : ''}
          <a class="btn btn-sm btn-outline-danger" href="/alumnos/expediente/${alumnoId}/documento/${doc.id}/eliminar/" data-confirm="¿Eliminar este documento del expediente?">Eliminar</a>
        </div>
      </div>
      <div class="expediente-card-body">
        <div><b>Fecha de emisión:</b> ${escapeHtml(doc.fecha_emision || '-')}</div>
        <div><b>Fecha de carga:</b> ${escapeHtml(doc.fecha_carga_label || doc.fecha_carga || '-')}</div>
        <div><b>Observaciones:</b> ${escapeHtml(doc.observaciones || '-')}</div>
      </div>
    </div>
  `).join('');
}

function renderHistorialActividad(containerId, historial) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const items = historial || [];
  if (!items.length) {
    container.innerHTML = '<div class="text-muted">No hay cambios registrados todavía.</div>';
    return;
  }

  container.innerHTML = items.map((item) => `
    <div class="expediente-card">
      <div class="expediente-card-header">
        <div>
          <div class="expediente-card-title">${escapeHtml(item.accion || 'Cambio registrado')}</div>
          <div class="text-muted small">${escapeHtml(item.fecha_hora || '-')}</div>
        </div>
        <span class="badge-doc-ok">${escapeHtml(item.correo_electronico || 'Sin correo')}</span>
      </div>
      <div class="expediente-card-body">
        <div><b>Entidad:</b> ${escapeHtml(item.entidad || '-')} #${escapeHtml(item.objeto_id || '-')}</div>
        <div><b>Detalle:</b> ${escapeHtml(item.descripcion || '-')}</div>
      </div>
    </div>
  `).join('');
}

function renderHistorialAcademico(containerId, historial) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const data = historial || {};
  const resumen = data.resumen || {};
  const calificaciones = data.calificaciones_por_periodo || [];
  const asistencia = data.asistencia || {};
  const observaciones = data.observaciones || [];
  const historialAnual = data.historial_anual || [];

  const resumenHtml = `
    <div class="academic-summary-grid">
      <div class="academic-summary-card">
        <div class="academic-summary-label">Promedio general</div>
        <div class="academic-summary-value">${resumen.promedio_general ?? '-'}</div>
      </div>
      <div class="academic-summary-card">
        <div class="academic-summary-label">Asistencia</div>
        <div class="academic-summary-value">${resumen.asistencia_porcentaje ?? '-'}%</div>
      </div>
      <div class="academic-summary-card">
        <div class="academic-summary-label">Conducta</div>
        <div class="academic-summary-value">${escapeHtml(resumen.conducta_actual_label || 'Sin observaciones')}</div>
      </div>
      <div class="academic-summary-card">
        <div class="academic-summary-label">Observaciones</div>
        <div class="academic-summary-value">${resumen.observaciones_total ?? 0}</div>
      </div>
    </div>
  `;

  const calificacionesHtml = calificaciones.map((periodo) => {
    const items = (periodo.items || []).map((item) => `
      <div class="academic-row">
        <div>
          <strong>${escapeHtml(item.materia || '-')}</strong>
          <small>${escapeHtml(item.docente || 'Sin docente')}</small>
        </div>
        <div class="academic-pill academic-pill-blue">${item.nota ?? '-'}</div>
      </div>
    `).join('');

    return `
      <div class="academic-section">
        <div class="academic-section-header">
          <div class="academic-section-title">${escapeHtml(periodo.periodo_label || 'Período')}</div>
          <div class="d-flex gap-2 flex-wrap">
            <span class="academic-pill academic-pill-green">${periodo.cantidad ?? 0} calificaciones</span>
            <span class="academic-pill academic-pill-amber">Promedio: ${periodo.promedio ?? '-'}</span>
          </div>
        </div>
        <div class="academic-section-body">
          ${items || '<div class="academic-empty">No hay calificaciones cargadas para este período.</div>'}
        </div>
      </div>
    `;
  }).join('');

  const asistenciaItems = (asistencia.items || []).map((item) => `
    <div class="academic-row">
      <div>
        <strong>${escapeHtml(item.materia || '-')}</strong>
        <small>${escapeHtml(item.fecha || '-')} · ${escapeHtml(item.docente || 'Sin docente')}</small>
      </div>
      <div class="academic-pill ${item.estado === 'P' ? 'academic-pill-green' : item.estado === 'A' ? 'academic-pill-amber' : 'academic-pill-blue'}">${escapeHtml(item.estado_label || item.estado || '-')}</div>
    </div>
  `).join('');

  const observacionesItems = observaciones.map((item) => `
    <div class="academic-row">
      <div>
        <strong>${escapeHtml(item.conducta_label || 'Observación')}</strong>
        <small>${escapeHtml(item.fecha || '-')} · ${escapeHtml(item.periodo_label || 'General')} · ${escapeHtml(item.creado_por || 'Sistema')}</small>
        <div class="mt-1">${escapeHtml(item.observacion || '')}</div>
      </div>
      <div class="academic-pill academic-pill-blue">${escapeHtml(item.conducta_label || '-')}</div>
    </div>
  `).join('');

  const historialAnualHtml = historialAnual.length
    ? `
      <div class="academic-section">
        <div class="academic-section-header">
          <div class="academic-section-title">Historial académico por año lectivo</div>
        </div>
        <div class="academic-section-body">
          <div class="table-responsive">
            <table class="table table-sm align-middle mb-0">
              <thead>
                <tr>
                  <th>Año lectivo</th>
                  <th>Curso</th>
                  <th>División</th>
                  <th>Estado alumno</th>
                  <th>Resultado final</th>
                  <th>Fecha promoción</th>
                  <th>Fecha baja</th>
                  <th>Estado promoción</th>
                  <th>Motivo no promoción</th>
                </tr>
              </thead>
              <tbody>
                ${historialAnual.map((h) => `
                  <tr>
                    <td>${escapeHtml(String(h.anio_lectivo || '-'))}</td>
                    <td>${escapeHtml(String(h.curso || '-'))}°</td>
                    <td>${escapeHtml(h.division || '-')}</td>
                    <td>${escapeHtml(h.estado_alumno || '-')}</td>
                    <td>${escapeHtml(h.resultado_final || '-')}</td>
                    <td>${escapeHtml(h.fecha_promocion || '-')}</td>
                    <td>${escapeHtml(h.fecha_baja || '-')}</td>
                    <td>${escapeHtml(h.estado_promocion_label || '-')}</td>
                    <td>${escapeHtml(h.motivo_no_promocion || '-')}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `
    : '<div class="academic-empty">El alumno todavía no posee historial académico registrado.</div>';

  container.innerHTML = `
    ${historialAnualHtml}
    ${resumenHtml}
    <div class="academic-section">
      <div class="academic-section-header">
        <div class="academic-section-title">Calificaciones por período</div>
      </div>
      <div class="academic-section-body academic-list">
        ${calificacionesHtml || '<div class="academic-empty">No hay calificaciones cargadas.</div>'}
      </div>
    </div>
    <div class="academic-section">
      <div class="academic-section-header">
        <div class="academic-section-title">Asistencia acumulada</div>
        <div class="d-flex gap-2 flex-wrap">
          <span class="academic-pill academic-pill-green">Presentes: ${asistencia.por_estado?.P ?? 0}</span>
          <span class="academic-pill academic-pill-amber">Ausentes: ${asistencia.por_estado?.A ?? 0}</span>
          <span class="academic-pill academic-pill-blue">Tardanzas: ${asistencia.por_estado?.T ?? 0}</span>
        </div>
      </div>
      <div class="academic-section-body academic-list">
        ${asistenciaItems || '<div class="academic-empty">No hay asistencia cargada.</div>'}
      </div>
    </div>
    <div class="academic-section">
      <div class="academic-section-header">
        <div class="academic-section-title">Observaciones y conducta</div>
      </div>
      <div class="academic-section-body academic-list">
        ${observacionesItems || '<div class="academic-empty">No hay observaciones cargadas.</div>'}
      </div>
    </div>
  `;
}

function renderObservacionesEditable(containerId, alumnoId, historial, puedeEditar) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const data = historial || {};
  const observaciones = data.observaciones || [];

  if (!observaciones.length) {
    container.innerHTML = '<div class="academic-empty">No hay observaciones cargadas.</div>';
    return;
  }

  container.innerHTML = observaciones.map((item) => {
    const removeAction = puedeEditar
      ? `<a class="btn btn-sm btn-outline-danger" data-confirm="\u00BFEliminar observaci\u00F3n?" href="/alumnos/academico/${alumnoId}/observacion/${item.id}/eliminar/">Eliminar</a>`
      : '<span class="badge-doc-missing">Solo lectura</span>';

    return `
      <div class="academic-row">
        <div>
          <strong>${escapeHtml(item.conducta_label || 'Observaci\u00F3n')}</strong>
          <small>${escapeHtml(item.fecha || '-')} · ${escapeHtml(item.periodo_label || 'General')} · ${escapeHtml(item.creado_por || 'Sistema')}</small>
          <div class="mt-1">${escapeHtml(item.observacion || '')}</div>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="academic-pill academic-pill-blue">${escapeHtml(item.conducta_label || '-')}</span>
          ${removeAction}
        </div>
      </div>
    `;
  }).join('');
}

function abrirModalExpediente(alumnoId, documento = null) {
  const modalEl = document.getElementById('modalExpediente');
  const modal = new bootstrap.Modal(modalEl);
  const form = document.getElementById('formExpediente');
  const title = document.getElementById('expedienteModalTitle');
  const alumnoInput = document.getElementById('expediente-alumno-id');
  const idInput = document.getElementById('expediente-id');
  const nombreInput = document.getElementById('expediente-nombre-documento');
  const tipoInput = document.getElementById('expediente-tipo-documento');
  const fechaInput = document.getElementById('expediente-fecha-emision');
  const estadoInput = document.getElementById('expediente-estado');
  const archivoInput = document.getElementById('expediente-archivo');
  const observacionesInput = document.getElementById('expediente-observaciones');

  if (!form || !alumnoInput || !idInput) return;

  form.action = `/alumnos/expediente/${alumnoId}/documento/guardar/`;
  alumnoInput.value = alumnoId;
  idInput.value = documento?.id || '';
  nombreInput.value = documento?.nombre_documento || '';
  tipoInput.value = documento?.tipo_documento || 'otro';
  fechaInput.value = normalizeDateForInput(documento?.fecha_emision || '');
  estadoInput.value = documento?.estado || 'vigente';
  observacionesInput.value = documento?.observaciones || '';
  if (archivoInput) archivoInput.value = '';
  if (title) title.textContent = documento ? 'Editar documento de expediente' : 'Nuevo documento de expediente';

  modal.show();
}

function irAContactoResponsables(alumnoId, agregarNuevo = false) {
  const editButton = document.querySelector(`.js-editar-alumno[data-id="${alumnoId}"]`);
  if (!editButton) return;

  __ultimoAlumnoIdEditar = editButton.dataset.id;
  editarAlumno(
    editButton.dataset.id,
    editButton.dataset.nombre,
    editButton.dataset.apellido,
    editButton.dataset.dni,
    editButton.dataset.tipoIdentificacion,
    editButton.dataset.fecha,
    editButton.dataset.domicilio,
    editButton.dataset.telefono,
    editButton.dataset.anio,
    editButton.dataset.division,
    editButton.dataset.activo
  );

  const modalVerEl = document.getElementById('modalVer');
  if (modalVerEl) {
    const modalVerInst = bootstrap.Modal.getInstance(modalVerEl);
    if (modalVerInst) modalVerInst.hide();
  }

  setTimeout(() => {
    const tabTrigger = document.getElementById('tab-editar-contacto');
    if (tabTrigger) {
      const tab = new bootstrap.Tab(tabTrigger);
      tab.show();
    }

    if (agregarNuevo) {
      const btnAdd = document.getElementById('btnAddResponsableEditar');
      if (btnAdd) btnAdd.click();
    }
  }, 220);
}

async function verAlumno(id) {
  const modalEl = document.getElementById('modalVer');
  const modal = new bootstrap.Modal(modalEl);

  const contTut = document.getElementById('tutoresContainer');
  const contRet = document.getElementById('retiroContainer');
  if (contTut) contTut.innerHTML = '<div class="text-muted">Cargando responsables...</div>';
  if (contRet) contRet.innerHTML = '<div class="text-muted">Cargando retiro...</div>';

  const res = await fetch(`/alumnos/${id}/ficha/?_=${Date.now()}`, {
    cache: 'no-store',
  });
  const data = await res.json();

  const a = data.alumno;
  const puedeEditarHistorial = !!(data.permisos && data.permisos.puede_editar_historial);

  document.getElementById('v-id').textContent = a.id;
  document.getElementById('v-nombre').textContent = a.apellido + ', ' + a.nombre;
  document.getElementById('v-dni').textContent = a.dni;
  document.getElementById('v-tipo-identificacion').textContent = a.tipo_identificacion_label || 'Documento';
  document.getElementById('v-fecha').textContent = formatDateForDisplay(a.fecha_nacimiento);
  const edad = calcularEdad(a.fecha_nacimiento);
  document.getElementById('v-edad').textContent = edad === null ? '-' : `${edad} años`;
  document.getElementById('v-domicilio').textContent = a.domicilio;
  document.getElementById('v-telefono').textContent = a.telefono;
  document.getElementById('v-curso').textContent = a.curso;
  document.getElementById('v-estado').innerHTML = a.estado === 'Activo'
    ? '<span class="badge-activo">Activo</span>'
    : '<span class="badge-inactivo">Inactivo</span>';
  const estadoPromocionEl = document.getElementById('v-estado-promocion');
  if (estadoPromocionEl) {
    estadoPromocionEl.innerHTML = a.estado_promocion === 'promocionado'
      ? '<span class="badge-activo">Promocionado</span>'
      : '<span class="badge-inactivo">No Promocionado</span>';
  }
  const motivoNoPromEl = document.getElementById('v-motivo-no-promocion');
  if (motivoNoPromEl) motivoNoPromEl.textContent = a.motivo_no_promocion || '-';
  document.getElementById('v-fecha-baja').textContent = a.fecha_baja || '-';
  document.getElementById('v-motivo-baja').textContent = a.motivo_baja || '-';
  const docEstadoEl = document.getElementById('v-documentacion-estado');
  if (docEstadoEl) {
    if (a.documentacion_total > 0) {
      docEstadoEl.innerHTML = a.documentacion_completa
        ? '<span class="badge-doc-ok">Documentación completa</span>'
        : `<span class="badge-doc-missing">Falta: ${a.documentacion_faltante.join(', ')}</span>`;
    } else {
      docEstadoEl.innerHTML = '<span class="badge-doc-missing">Sin archivos cargados</span>';
    }
  }
  const certBajaEl = document.getElementById('v-certificado-baja');
  if (certBajaEl) {
    certBajaEl.innerHTML = a.certificado_baja_url
      ? `<a href="${a.certificado_baja_url}" target="_blank" rel="noopener">Ver certificado PDF</a>`
      : '-';
  }

  prepararBotonesExpediente(a.id);
  renderExpedienteDocumentos('expedienteContainer', a.id, data.expediente_documentos || []);
  renderHistorialActividad('historialActividadContainer', data.historial_actividad || []);

  const responsablesHtml = (data.responsables || []).map((r) => {
    const perimetralClass = r.perimetral ? 'responsable-con-perimetral' : (!r.puede_retirar ? 'responsable-no-retiro' : '');
    const retiroBadge = r.puede_retirar
      ? '<span class="badge-activo" style="font-size:0.72rem;">Puede retirar</span>'
      : '<span class="badge-inactivo" style="font-size:0.72rem;">No puede retirar</span>';

    return `
      <div class="sge-card responsable-card-pro ${perimetralClass}" style="margin-bottom:12px;">
        <div class="sge-card-header responsable-card-header-pro">
          <div>
            <div class="responsable-name">${escapeHtml(r.apellido || '')}, ${escapeHtml(r.nombre || '')}</div>
            <div class="responsable-role">${escapeHtml(r.tipo_responsable || 'Responsable')}</div>
          </div>
          <div>${retiroBadge}</div>
        </div>
        <div class="sge-card-body">
          <div class="responsable-grid-pro">
            <section class="responsable-section">
              <h6>Identidad</h6>
              <div><b>DNI:</b> ${escapeHtml(r.dni || '-')}</div>
              <div><b>Fecha nacimiento:</b> ${escapeHtml(r.fecha_nacimiento || '-')}</div>
              <div><b>Parentesco:</b> ${escapeHtml(r.parentesco || '-')}</div>
            </section>

            <section class="responsable-section">
              <h6>Contacto</h6>
              <div><b>Teléfono:</b> ${escapeHtml(r.telefono || '-')}</div>
              <div><b>Teléfono alt.:</b> ${escapeHtml(r.telefono_alternativo || '-')}</div>
              <div><b>Correo:</b> ${escapeHtml(r.correo_electronico || '-')}</div>
            </section>

            <section class="responsable-section responsable-section-wide">
              <h6>Domicilio</h6>
              <div><b>${escapeHtml(r.domicilio || '-')}</b></div>
              <div>${escapeHtml([r.localidad, r.provincia, r.codigo_postal].filter(Boolean).join(' - ') || '-')}</div>
            </section>

            <section class="responsable-section">
              <h6>Perfil laboral</h6>
              <div><b>Ocupación:</b> ${escapeHtml(r.ocupacion || '-')}</div>
              <div><b>Lugar de trabajo:</b> ${escapeHtml(r.lugar_trabajo || '-')}</div>
              <div><b>Nacionalidad:</b> ${escapeHtml(r.nacionalidad || '-')}</div>
              <div><b>Profesión:</b> ${escapeHtml(r.profesion || '-')}</div>
            </section>

            <section class="responsable-section">
              <h6>Documentación</h6>
              <div><b>Antivariolico:</b> ${escapeHtml(r.certificado_antivariolico || '-')}</div>
              <div><b>Antidifterico:</b> ${escapeHtml(r.certificado_antidifterico || '-')}</div>
              <div><b>Antipolio:</b> ${escapeHtml(r.certificado_antipolio || '-')}</div>
              <div><b>Bucodental:</b> ${escapeHtml(r.certificado_buco_dental || '-')}</div>
            </section>

            <section class="responsable-section">
              <h6>Restricciones y notas</h6>
              <div><b>Perimetral:</b> ${r.perimetral ? 'Si (PDF cargado)' : 'No'}</div>
              ${r.perimetral ? `<div><b>Motivo:</b> ${escapeHtml(r.perimetral_motivo || '-')}</div>` : ''}
              <div><b>Anotaciones:</b> ${escapeHtml(r.anotaciones_particulares || '-')}</div>
              <div><b>Observaciones:</b> ${escapeHtml(r.observaciones || '-')}</div>
            </section>
          </div>
        </div>
      </div>
    `;
  }).join('');

  const retiroHtml = `
    <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap mb-3">
      <h6 class="mb-0">Autorización de retiro</h6>
      <button type="button" class="btn btn-primary-custom js-add-responsable-retiro" data-alumno-id="${id}">
        + Agregar nuevo responsable
      </button>
    </div>
    ${(data.responsables || []).length
      ? (data.responsables || []).map((r) => `
          <div class="sge-card ${r.perimetral ? 'responsable-con-perimetral' : (!r.puede_retirar ? 'responsable-no-retiro' : '')}" style="margin-bottom:10px;">
            <div class="sge-card-body py-2">
              <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap">
                <div>
                  <b>${r.apellido}, ${r.nombre}</b>
                  <span class="text-muted">(${r.tipo_responsable || 'Responsable'})</span>
                  ${r.perimetral ? `<span class="badge-perimetral ms-2">Perimetral vigente</span><span class="badge-perimetral-motivo ms-2">Motivo: ${r.perimetral_motivo || 'Sin detalle'}</span>` : ''}
                </div>
                <div>
                  ${r.puede_retirar
                    ? '<span class="badge-activo">Autorizado para retirar</span>'
                    : '<span class="badge-inactivo">No autorizado para retirar</span>'}
                </div>
              </div>
            </div>
          </div>
        `).join('')
      : '<div class="text-muted">No hay responsables cargados.</div>'}
    <button type="button" class="btn btn-outline-secondary js-open-contacto-responsables" data-alumno-id="${id}">
      Editar responsables en Contacto
    </button>
  `;

  if (contTut) contTut.innerHTML = responsablesHtml || '<div class="text-muted">No existen padres, tutores o encargados asociados a este alumno.</div>';

  if (contRet) contRet.innerHTML = retiroHtml;

  renderExpedienteDocumentos('expedienteEditarContainer', a.id, data.expediente_documentos || []);
  renderHistorialActividad('historialActividadEditarContainer', data.historial_actividad || []);

  modal.show();
}







function editarAlumno(id, nombre, apellido, dni, tipoIdentificacion, fecha, domicilio, telefono, anio, division, activo, documentacionArchivosRaw, documentacionCompletaKeysRaw) {
  document.getElementById('formEditar').action = '/alumnos/editar/' + id + '/';

  document.getElementById('e-nombre').value = nombre;
  document.getElementById('e-apellido').value = apellido;
  document.getElementById('e-dni').value = dni;
  const eTipo = document.getElementById('e-tipo-identificacion');
  if (eTipo) {
    eTipo.value = tipoIdentificacion || 'documento';
  }
  actualizarLabelIdentificacion('e');
  setDateControlValue('e-fecha', fecha);
  actualizarEdadEditarAlumno();
  document.getElementById('e-domicilio').value = domicilio;
  document.getElementById('e-telefono').value = telefono;
  document.getElementById('e-anio').value = anio;
  document.getElementById('e-division').value = division;
  document.getElementById('e-activo').value = activo;
  __documentosExistentesEditar = parseDocumentacionArchivos(documentacionArchivosRaw);
  __documentosCompletosEditarKeys = parseDocumentacionKeys(documentacionCompletaKeysRaw);
  clearRequiredDocSelections('e');
  const eDocExtraInput = document.getElementById('e-documentacion-extra');
  if (eDocExtraInput) eDocExtraInput.value = '';
  actualizarEstadoDocumentacionEditar();

  const cont = document.getElementById('editarTutoresContacto');
  if (cont) cont.innerHTML = '<div class="text-muted">Cargando padres/tutores...</div>';

  fetch('/alumnos/' + id + '/ficha/')
    .then((r) => r.json())
    .then((data) => {
      const responsables = data.responsables || [];
      prepararBotonesExpediente(id);
      renderExpedienteDocumentos('expedienteEditarContainer', id, data.expediente_documentos || []);
      renderHistorialActividad('historialActividadEditarContainer', data.historial_actividad || []);

      // Render usando el módulo nuevo (sin legacy)
      if (typeof cargarResponsables === 'function') {
        cargarResponsables(cont, responsables);
      } else {
        // Fallback mínimo si no cargó el archivo .responsables.js
        cont.innerHTML = '<div class="text-danger">JS de responsables no cargado.</div>';
      }
    })
    .catch(() => {
      if (cont) cont.innerHTML = '<div class="text-muted">Error cargando padres/tutores.</div>';
    });

  new bootstrap.Modal(document.getElementById('modalEditar')).show();
}
/*toma los datos del alumno, los carga en el formulario de edicion y abre el modar para editarlos*/


// Delegación de eventos para acciones principales
let __ultimoAlumnoIdEditar = null;

document.addEventListener('click', function (event) {
  // Botón Ver alumno
  const verButton = event.target.closest('.js-ver-alumno');
  if (verButton) {
    verAlumno(verButton.dataset.id);
    return;
  }

  // Botón Editar alumno
  const editButton = event.target.closest('.js-editar-alumno');
  if (editButton) {
    __ultimoAlumnoIdEditar = editButton.dataset.id;
    editarAlumno(
      editButton.dataset.id,
      editButton.dataset.nombre,
      editButton.dataset.apellido,
      editButton.dataset.dni,
      editButton.dataset.tipoIdentificacion,
      editButton.dataset.fecha,
      editButton.dataset.domicilio,
      editButton.dataset.telefono,
      editButton.dataset.anio,
      editButton.dataset.division,
      editButton.dataset.activo,
      editButton.dataset.documentacionArchivos,
      editButton.dataset.documentacionCompletaKeys
    );
    return;
  }

  const btnOpenContacto = event.target.closest('.js-open-contacto-responsables');
  if (btnOpenContacto) {
    irAContactoResponsables(btnOpenContacto.dataset.alumnoId, false);
    return;
  }

  const btnOpenExpediente = event.target.closest('.js-open-expediente');
  if (btnOpenExpediente) {
    abrirModalExpediente(btnOpenExpediente.dataset.alumnoId);
    return;
  }

  const btnEditExpediente = event.target.closest('.js-edit-expediente');
  if (btnEditExpediente) {
    abrirModalExpediente(btnEditExpediente.dataset.alumnoId, {
      id: btnEditExpediente.dataset.documentoId,
      nombre_documento: btnEditExpediente.dataset.documentoNombre,
      tipo_documento: btnEditExpediente.dataset.documentoTipo,
      fecha_emision: btnEditExpediente.dataset.documentoFechaEmision,
      estado: btnEditExpediente.dataset.documentoEstado,
      observaciones: btnEditExpediente.dataset.documentoObservaciones,
    });
    return;
  }

  const btnAddResponsableRetiro = event.target.closest('.js-add-responsable-retiro');
  if (btnAddResponsableRetiro) {
    irAContactoResponsables(btnAddResponsableRetiro.dataset.alumnoId, true);
    return;
  }

  const btnAbrirBaja = event.target.closest('.js-abrir-baja');
  if (btnAbrirBaja) {
    const formBaja = document.getElementById('formBaja');
    const alumnoNombre = document.getElementById('bajaAlumnoNombre');
    const bajaFecha = document.getElementById('baja-fecha');

    if (formBaja) formBaja.action = '/alumnos/baja/' + btnAbrirBaja.dataset.id + '/';
    if (alumnoNombre) alumnoNombre.textContent = btnAbrirBaja.dataset.alumno || '-';
    if (bajaFecha && !bajaFecha.value) {
      const h = new Date();
      setDateControlValue('baja-fecha', `${h.getFullYear()}-${String(h.getMonth() + 1).padStart(2, '0')}-${String(h.getDate()).padStart(2, '0')}`);
    }

    new bootstrap.Modal(document.getElementById('modalBaja')).show();
    return;
  }

  // Confirmar enlaces con data-confirm
  const confirmLink = event.target.closest('[data-confirm]');
  if (confirmLink && !confirm(confirmLink.dataset.confirm)) {
    event.preventDefault();
  }
});

document.addEventListener('submit', function (event) {
  const form = event.target;
  if (!form || form.id !== 'formEditar') return;

  if (__ultimoAlumnoIdEditar) {
    // Guardar TODO en el mismo endpoint (sin legacy)
    form.action = '/alumnos/editar/' + __ultimoAlumnoIdEditar + '/';
  }
});

