/*
 * Справочник плейсхолдеров шаблонов (TemplatePlaceholdersAdminMixin).
 * Клик по чипу вставляет {placeholder} в последнее сфокусированное поле шаблона
 * (id_name_template / id_description_template) и копирует в буфер обмена.
 * «Скопировать все» кладёт весь список в буфер обмена.
 */
(function () {
  'use strict';

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(function () { legacyCopy(text); });
    } else {
      legacyCopy(text);
    }
  }

  function legacyCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) { /* ignore */ }
    document.body.removeChild(ta);
  }

  function insertAtCursor(field, text) {
    if (!field) return false;
    var start = field.selectionStart != null ? field.selectionStart : field.value.length;
    var end = field.selectionEnd != null ? field.selectionEnd : start;
    field.value = field.value.slice(0, start) + text + field.value.slice(end);
    field.selectionStart = field.selectionEnd = start + text.length;
    field.focus();
    return true;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var nameField = document.getElementById('id_name_template');
    var descField = document.getElementById('id_description_template');
    var lastFocused = nameField || descField;

    [nameField, descField].forEach(function (f) {
      if (!f) return;
      f.addEventListener('focus', function () { lastFocused = f; });
    });

    var help = document.querySelector('.template-placeholders-help');
    if (!help) return;

    help.addEventListener('click', function (e) {
      var chip = e.target.closest('.tp-chip');
      if (chip) {
        var ph = chip.getAttribute('data-ph');
        copyToClipboard(ph);
        if (!insertAtCursor(lastFocused || nameField || descField, ph)) {
          copyToClipboard(ph);
        }
        return;
      }
      var copyAll = e.target.closest('.tp-copy-all');
      if (copyAll) {
        copyToClipboard(copyAll.getAttribute('data-list'));
      }
    });
  });
})();
