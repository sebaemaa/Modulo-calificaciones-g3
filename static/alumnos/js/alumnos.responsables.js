// Funciones de UI para Responsables (Padres / Tutores)
// ES6+ (sin jQuery)

const RESPONSABLE_TIPO_OPTIONS = [
  { value: 'Tutor Responsable', label: 'Tutor Responsable' },
  { value: 'Tutor Secundario', label: 'Tutor Secundario' },
  { value: 'Padre', label: 'Padre' },
  { value: 'Madre', label: 'Madre' },
  { value: 'Abuelo', label: 'Abuelo' },
  { value: 'Abuela', label: 'Abuela' },
  { value: 'Hermano', label: 'Hermano' },
  { value: 'Hermana', label: 'Hermana' },
  { value: 'Familiar', label: 'Familiar' },
  { value: 'Tutor Legal', label: 'Tutor Legal' },
  { value: 'Otro Responsable', label: 'Otro' },
];

function escHtml(str) {
  return String(str ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function makeResponsableBlock({ index, responsableId = '' } = {}) {
  // IMPORTANTE: NO tarjetas anidadas; solo encabezado + formulario directo dentro del bloque.
  return `
  <div class="sge-card sge-responsable-block mb-3" data-responsable-index="${index}">
    <div class="sge-card-header">
      <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap">
        <div class="sge-responsable-head">
          <span class="js-encabezado-responsable">Apellido, Nombre</span>
        </div>
        <button type="button" class="btn btn-sm btn-outline-danger js-eliminar-responsable">
          Eliminar Responsable
        </button>
      </div>
    </div>

    <div class="sge-card-body">
      <input type="hidden" name="responsable_id[]" value="${escHtml(responsableId)}">
      <input type="hidden" name="n_orden[]" value="${index}">

      <div class="row g-3">
        <div class="col-md-4">
          <label class="form-label">Tipo de responsable</label>
          <select class="form-select js-tipo-responsable" name="tipo_responsable[]">
            <option value="">Seleccionar</option>
            ${RESPONSABLE_TIPO_OPTIONS.map((t) => `<option value="${escHtml(t.value)}">${escHtml(t.label)}</option>`).join('')}
          </select>
        </div>

        <div class="col-md-4">
          <label class="form-label">Nombre</label>
          <input type="text" class="form-control js-nombre-responsable" name="nombres[]" autocomplete="off">
        </div>

        <div class="col-md-4">
          <label class="form-label">Apellido</label>
          <input type="text" class="form-control js-apellido-responsable" name="apellidos[]" autocomplete="off">
        </div>

        <div class="col-md-4">
          <label class="form-label">DNI</label>
          <input type="text" class="form-control" name="dni[]">
        </div>

        <div class="col-md-4">
          <label class="form-label">Fecha de nacimiento</label>
          <input type="text" class="form-control js-fecha-responsable" name="fecha_nacimiento[]" placeholder="YYYY-MM-DD">
        </div>

        <div class="col-md-4 js-parentesco-wrap d-none">
          <label class="form-label">Parentesco</label>
          <input type="text" class="form-control" name="parentesco[]">
        </div>

        <div class="col-md-6">
          <label class="form-label">Teléfono</label>
          <input type="text" class="form-control" name="telefonos[]">
        </div>

        <div class="col-md-6">
          <label class="form-label">Teléfono alternativo</label>
          <input type="text" class="form-control" name="telefono_alternativo[]">
        </div>

        <div class="col-md-6">
          <label class="form-label">Correo electrónico</label>
          <input type="email" class="form-control" name="correo_electronico[]">
        </div>

        <div class="col-md-6">
          <label class="form-label">Ocupación</label>
          <input type="text" class="form-control" name="ocupacion[]">
        </div>

        <div class="col-md-6">
          <label class="form-label">Nacionalidad</label>
          <input type="text" class="form-control" name="nacionalidad[]">
        </div>

        <div class="col-md-6">
          <label class="form-label">Profesión</label>
          <input type="text" class="form-control" name="profesion[]">
        </div>

        <div class="col-12">
          <label class="form-label">Domicilio</label>
          <input type="text" class="form-control" name="domicilio[]">
        </div>

        <div class="col-md-4">
          <label class="form-label">Localidad</label>
          <input type="text" class="form-control" name="localidad[]">
        </div>

        <div class="col-md-4">
          <label class="form-label">Provincia</label>
          <input type="text" class="form-control" name="provincia[]">
        </div>

        <div class="col-md-4">
          <label class="form-label">Código postal</label>
          <input type="text" class="form-control" name="codigo_postal[]">
        </div>

        <div class="col-12">
          <label class="form-label">Lugar de trabajo</label>
          <input type="text" class="form-control" name="lugar_trabajo[]">
        </div>

        <div class="col-md-6">
          <label class="form-label">Certificado Antivariolico</label>
          <input type="hidden" name="cert_antivariolico[]" value="">
          <input type="file" class="form-control js-cert-antivariolico-file" name="cert_antivariolico_file_${index}" accept="application/pdf,.pdf">
          <div class="form-text js-cert-antivariolico-actual">Sin PDF cargado</div>
        </div>

        <div class="col-md-6">
          <label class="form-label">Certificado Antidifterico</label>
          <input type="hidden" name="cert_antidifterico[]" value="">
          <input type="file" class="form-control js-cert-antidifterico-file" name="cert_antidifterico_file_${index}" accept="application/pdf,.pdf">
          <div class="form-text js-cert-antidifterico-actual">Sin PDF cargado</div>
        </div>

        <div class="col-md-6">
          <label class="form-label">Certificado Antipolio</label>
          <input type="hidden" name="cert_antipolio[]" value="">
          <input type="file" class="form-control js-cert-antipolio-file" name="cert_antipolio_file_${index}" accept="application/pdf,.pdf">
          <div class="form-text js-cert-antipolio-actual">Sin PDF cargado</div>
        </div>

        <div class="col-md-6">
          <label class="form-label">Certificado Búco dental</label>
          <input type="hidden" name="cert_buco_dental[]" value="">
          <input type="file" class="form-control js-cert-buco-dental-file" name="cert_buco_dental_file_${index}" accept="application/pdf,.pdf">
          <div class="form-text js-cert-buco-dental-actual">Sin PDF cargado</div>
        </div>

        <div class="col-md-6">
          <label class="form-label">Tiene perimetral</label>
          <select class="form-select js-tiene-perimetral" name="perimetral_tiene[]">
            <option value="0" selected>No</option>
            <option value="1">Sí</option>
          </select>
        </div>

        <div class="col-md-6 js-perimetral-file-wrap d-none">
          <label class="form-label">Perimetral (PDF)</label>
          <input type="hidden" name="perimetral[]" value="">
          <input type="file" class="form-control js-perimetral-file" name="perimetral_file_${index}" accept="application/pdf,.pdf">
          <div class="form-text js-perimetral-actual">Sin PDF cargado</div>
        </div>

        <div class="col-12 js-perimetral-motivo-wrap d-none">
          <label class="form-label">Por qué tiene perimetral</label>
          <input type="text" class="form-control js-perimetral-motivo" name="perimetral_motivo[]" placeholder="Detalle breve del motivo">
        </div>

        <div class="col-md-12">
          <label class="form-label">Anotaciones particulares</label>
          <textarea class="form-control" name="anotaciones_particulares[]" rows="2"></textarea>
        </div>

        <div class="col-md-12">
          <div class="form-check">
            <input type="hidden" name="puede_retirar_flags[]" value="0" class="js-puede-retirar-flag">
            <input class="form-check-input js-puede-retirar" type="checkbox" name="puede_retirar_ui[]" value="1">
            <label class="form-check-label">Puede retirar</label>
          </div>
        </div>

        <div class="col-12">
          <label class="form-label">Observaciones</label>
          <textarea class="form-control" name="observaciones[]" rows="2"></textarea>
        </div>
      </div>
    </div>
  </div>
  `;
}

function actualizarEncabezado(bloque) {
  const apellido = (bloque.querySelector('.js-apellido-responsable')?.value || '').trim();
  const nombre = (bloque.querySelector('.js-nombre-responsable')?.value || '').trim();
  const encabezado = bloque.querySelector('.js-encabezado-responsable');
  if (encabezado) encabezado.textContent = apellido || nombre ? `${apellido || '-'}, ${nombre || '-'}` : 'Apellido, Nombre';
}

function initResponsableDatePicker(bloque) {
  if (typeof flatpickr !== 'function') return;
  const input = bloque.querySelector('.js-fecha-responsable');
  if (!input || input._flatpickr) return;
  flatpickr(input, {
    dateFormat: 'Y-m-d',
    allowInput: true,
  });
}

function updateCertInputNames(bloque, index) {
  const map = [
    ['cert_antivariolico_file_', 'js-cert-antivariolico-file'],
    ['cert_antidifterico_file_', 'js-cert-antidifterico-file'],
    ['cert_antipolio_file_', 'js-cert-antipolio-file'],
    ['cert_buco_dental_file_', 'js-cert-buco-dental-file'],
    ['perimetral_file_', 'js-perimetral-file'],
  ];

  map.forEach(([prefix, cls]) => {
    const input = bloque.querySelector(`.${cls}`);
    if (input) input.name = `${prefix}${index}`;
  });
}

function markCertInputs(bloque, index) {
  const certInputA = bloque.querySelector(`input[name="cert_antivariolico_file_${index}"]`);
  if (certInputA) certInputA.classList.add('js-cert-antivariolico-file');
  const certInputD = bloque.querySelector(`input[name="cert_antidifterico_file_${index}"]`);
  if (certInputD) certInputD.classList.add('js-cert-antidifterico-file');
  const certInputP = bloque.querySelector(`input[name="cert_antipolio_file_${index}"]`);
  if (certInputP) certInputP.classList.add('js-cert-antipolio-file');
  const certInputB = bloque.querySelector(`input[name="cert_buco_dental_file_${index}"]`);
  if (certInputB) certInputB.classList.add('js-cert-buco-dental-file');
  const perimetralInput = bloque.querySelector(`input[name="perimetral_file_${index}"]`);
  if (perimetralInput) perimetralInput.classList.add('js-perimetral-file');
}

function toggleParentescoVisibility(bloque) {
  const select = bloque.querySelector('.js-tipo-responsable');
  const wrap = bloque.querySelector('.js-parentesco-wrap');
  const input = bloque.querySelector('[name="parentesco[]"]');
  if (!select || !wrap || !input) return;

  const isOtro = (select.value || '').trim() === 'Otro Responsable';
  wrap.classList.toggle('d-none', !isOtro);
  input.required = isOtro;
  if (!isOtro) input.value = '';
}

function togglePerimetralFileVisibility(bloque) {
  const select = bloque.querySelector('.js-tiene-perimetral');
  const wrap = bloque.querySelector('.js-perimetral-file-wrap');
  const fileInput = bloque.querySelector('.js-perimetral-file');
  const actual = bloque.querySelector('.js-perimetral-actual');
  const motivoWrap = bloque.querySelector('.js-perimetral-motivo-wrap');
  const motivoInput = bloque.querySelector('.js-perimetral-motivo');
  if (!select || !wrap || !fileInput) return;

  const enabled = (select.value || '0') === '1';
  wrap.classList.toggle('d-none', !enabled);
  fileInput.disabled = !enabled;

  if (motivoWrap && motivoInput) {
    motivoWrap.classList.toggle('d-none', !enabled);
    motivoInput.required = enabled;
    if (!enabled) motivoInput.value = '';
  }

  if (!enabled && actual) {
    actual.textContent = 'Sin PDF cargado';
  }
}

function reordenarResponsables(contenedor) {
  const bloques = Array.from(contenedor.querySelectorAll('.js-eliminar-responsable')).map(btn => btn.closest('.sge-responsable-block'));
  bloques.forEach((bloque, idx) => {
    const newIndex = idx + 1;
    bloque.dataset.responsableIndex = newIndex;
    const hiddenOrden = bloque.querySelector('input[name="n_orden[]"]');
    if (hiddenOrden) hiddenOrden.value = newIndex;
    updateCertInputNames(bloque, newIndex);
  });
}

function eliminarResponsable(contenedor, boton) {
  const bloque = boton.closest('.sge-responsable-block');
  if (!bloque) return;
  const ok = confirm('¿Eliminar Responsable?');
  if (!ok) return;
  bloque.remove();
  reordenarResponsables(contenedor);
}

function bindResponsableBlockEvents(bloque, contenedor) {
  bloque.querySelectorAll('.js-apellido-responsable, .js-nombre-responsable').forEach((el) => {
    el.addEventListener('input', () => actualizarEncabezado(bloque));
  });

  const chkRetiro = bloque.querySelector('.js-puede-retirar');
  const retiroFlag = bloque.querySelector('.js-puede-retirar-flag');
  if (chkRetiro && retiroFlag) {
    const syncRetiro = () => { retiroFlag.value = chkRetiro.checked ? '1' : '0'; };
    chkRetiro.addEventListener('change', syncRetiro);
    syncRetiro();
  }

  const selectTipo = bloque.querySelector('.js-tipo-responsable');
  if (selectTipo) {
    selectTipo.addEventListener('change', () => toggleParentescoVisibility(bloque));
    toggleParentescoVisibility(bloque);
  }

  const selectPerimetral = bloque.querySelector('.js-tiene-perimetral');
  if (selectPerimetral) {
    selectPerimetral.addEventListener('change', () => togglePerimetralFileVisibility(bloque));
    togglePerimetralFileVisibility(bloque);
  }

  initResponsableDatePicker(bloque);

}

function cargarResponsables(contenedor, data = []) {
  // data: [{id,tipo_responsable,nombre,apellido,...}]
  contenedor.innerHTML = '';
  if (!data.length) {
    // crear un bloque vacío
    agregarResponsable(contenedor, null);
    return;
  }
  data.forEach((d, i) => {
    const html = makeResponsableBlock({ index: i + 1, responsableId: d.id || '' });
    contenedor.insertAdjacentHTML('beforeend', html);
    const bloque = contenedor.querySelector(`.sge-responsable-block[data-responsable-index="${i + 1}"]`);
    if (!bloque) return;
    markCertInputs(bloque, i + 1);

    if (d.tipo_responsable) bloque.querySelector('select.js-tipo-responsable').value = d.tipo_responsable;
    if (d.nombre) bloque.querySelector('.js-nombre-responsable').value = d.nombre;
    if (d.apellido) bloque.querySelector('.js-apellido-responsable').value = d.apellido;

    // Se completan los demás campos si llegan
    const setVal = (name, value) => {
      const el = bloque.querySelector(`[name="${name}[]"]`);
      if (el) el.value = value ?? '';
    };
    setVal('dni', d.dni);
    setVal('fecha_nacimiento', d.fecha_nacimiento);
    setVal('parentesco', d.parentesco);
    setVal('telefonos', d.telefono);
    setVal('telefono_alternativo', d.telefono_alternativo);
    setVal('correo_electronico', d.correo_electronico);
    setVal('domicilio', d.domicilio);
    setVal('localidad', d.localidad);
    setVal('provincia', d.provincia);
    setVal('codigo_postal', d.codigo_postal);
    setVal('ocupacion', d.ocupacion);
    setVal('lugar_trabajo', d.lugar_trabajo);
    setVal('observaciones', d.observaciones);

    // Campos adicionales
    setVal('nacionalidad', d.nacionalidad);
    setVal('profesion', d.profesion);
    setVal('cert_antivariolico', d.certificado_antivariolico);
    setVal('cert_antidifterico', d.certificado_antidifterico);
    setVal('cert_antipolio', d.certificado_antipolio);
    setVal('cert_buco_dental', d.certificado_buco_dental);
    setVal('perimetral', d.perimetral);
    setVal('perimetral_motivo', d.perimetral_motivo);
    setVal('anotaciones_particulares', d.anotaciones_particulares);

    const perimetralFlag = bloque.querySelector('.js-tiene-perimetral');
    if (perimetralFlag) perimetralFlag.value = d.perimetral ? '1' : '0';

    // puede_retirar
    const chkRetiro = bloque.querySelector('.js-puede-retirar');
    const retiroFlag = bloque.querySelector('.js-puede-retirar-flag');
    if (chkRetiro) chkRetiro.checked = !!d.puede_retirar;
    if (retiroFlag) retiroFlag.value = d.puede_retirar ? '1' : '0';

    const certA = bloque.querySelector('.js-cert-antivariolico-actual');
    const certD = bloque.querySelector('.js-cert-antidifterico-actual');
    const certP = bloque.querySelector('.js-cert-antipolio-actual');
    const certB = bloque.querySelector('.js-cert-buco-dental-actual');
    const perimetralActual = bloque.querySelector('.js-perimetral-actual');

    if (certA) certA.textContent = d.certificado_antivariolico ? `Actual: ${d.certificado_antivariolico}` : 'Sin PDF cargado';
    if (certD) certD.textContent = d.certificado_antidifterico ? `Actual: ${d.certificado_antidifterico}` : 'Sin PDF cargado';
    if (certP) certP.textContent = d.certificado_antipolio ? `Actual: ${d.certificado_antipolio}` : 'Sin PDF cargado';
    if (certB) certB.textContent = d.certificado_buco_dental ? `Actual: ${d.certificado_buco_dental}` : 'Sin PDF cargado';
    if (perimetralActual) perimetralActual.textContent = d.perimetral ? `Actual: ${d.perimetral}` : 'Sin PDF cargado';

    bindResponsableBlockEvents(bloque, contenedor);

    actualizarEncabezado(bloque);
  });
}

function agregarResponsable(contenedor, data = null) {
  const currentCount = contenedor.querySelectorAll('.sge-responsable-block').length;
  const index = currentCount + 1;
  const html = makeResponsableBlock({ index, responsableId: data?.id || '' });
  contenedor.insertAdjacentHTML('beforeend', html);

  const bloque = contenedor.querySelector(`.sge-responsable-block[data-responsable-index="${index}"]`);
  if (!bloque) return;
  markCertInputs(bloque, index);

  if (data) {
    // mínimo: encabezado
    const apellido = data.apellido || '';
    const nombre = data.nombre || '';
    bloque.querySelector('.js-apellido-responsable').value = apellido;
    bloque.querySelector('.js-nombre-responsable').value = nombre;
  }

  updateCertInputNames(bloque, index);
  bindResponsableBlockEvents(bloque, contenedor);

  actualizarEncabezado(bloque);
}

function sincronizarResponsables(contenedor) {
  // por ahora solo reordena en base al orden DOM
  reordenarResponsables(contenedor);
}

// Las funciones son globales (declaradas con function), no se necesita export.

// Crear bloque inicial para Nuevo Alumno al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  const contNuevo = document.getElementById('responsablesNuevoContainer');
  if (contNuevo && contNuevo.children.length === 0) {
    agregarResponsable(contNuevo);
  }
});

// Inicialización de botones por delegación (no requiere DOMContentLoaded)
// Funciona incluso si este script se carga después de alumnos.js
document.addEventListener('click', function(e) {
  // Botón "+ Agregar Responsable" en formulario NUEVO alumno
  if (e.target.closest('#btnAddResponsableNuevo')) {
    const cont = document.getElementById('responsablesNuevoContainer');
    if (cont) agregarResponsable(cont);
    return;
  }

  // Botón "+ Agregar Responsable" en EDICIÓN
  if (e.target.closest('#btnAddResponsableEditar')) {
    const cont = document.getElementById('editarTutoresContacto');
    if (cont) {
      if (cont.textContent && cont.textContent.trim().toLowerCase().includes('cargando')) {
        cont.innerHTML = '';
      }
      agregarResponsable(cont);
    }
    return;
  }

  // Botón Eliminar Responsable
  const elimBtn = e.target.closest('.js-eliminar-responsable');
  if (elimBtn) {
    const bloque = elimBtn.closest('.sge-responsable-block');
    if (bloque && confirm('¿Eliminar Responsable?')) {
      const contenedor = bloque.closest('[id$="Container"], .tutores-edit-container');
      bloque.remove();
      if (typeof reordenarResponsables === 'function' && contenedor) {
        reordenarResponsables(contenedor);
      }
    }
    return;
  }
});


