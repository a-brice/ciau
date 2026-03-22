/**
 * CIAU Architecture — main.js
 * Scoped to page type via data-page attribute on <body>.
 */

(function () {
  'use strict';

  const page = document.body.dataset.page || '';

  // -------------------------------------------------------------------------
  // Global: disable buttons on form submit to prevent double-submission
  // -------------------------------------------------------------------------
  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function () {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = btn.textContent + '…';
      }
    });
  });

  // -------------------------------------------------------------------------
  // Global: close open <details> when clicking outside
  // -------------------------------------------------------------------------
  document.addEventListener('click', function (e) {
    document.querySelectorAll('details[open]').forEach(function (det) {
      if (!det.contains(e.target)) {
        det.removeAttribute('open');
      }
    });
  });

  // -------------------------------------------------------------------------
  // Dashboard: auto-submit filter form on etat select change
  // -------------------------------------------------------------------------
  if (page === 'dashboard') {
    const etatSelect = document.querySelector('select[name="etat"]');
    if (etatSelect) {
      etatSelect.addEventListener('change', function () {
        this.closest('form').submit();
      });
    }
  }

  // -------------------------------------------------------------------------
  // Project detail: highlight overdue rows
  // -------------------------------------------------------------------------
  if (page === 'project-detail') {
    // Auto-open collect date input when clicking "Encaisser" container
    document.querySelectorAll('input[name="date_encaissement"]').forEach(function (input) {
      if (!input.value) {
        // Set default to today
        const today = new Date().toISOString().split('T')[0];
        input.value = today;
      }
    });
  }

})();
