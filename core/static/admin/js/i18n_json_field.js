/* core/static/admin/js/i18n_json_field.js
   Для textarea.i18n-json-field (поля переводов *_i18n в админке):
   кнопка «Форматировать» и подсветка валидности JSON при потере фокуса. */
(function () {
  'use strict';

  function setState(ta, ok, message) {
    ta.classList.remove('json-valid', 'json-invalid');
    ta.classList.add(ok ? 'json-valid' : 'json-invalid');
    var holder = ta.parentElement;
    var err = holder.querySelector('.json-error');
    if (!ok) {
      if (!err) {
        err = document.createElement('div');
        err.className = 'json-error';
        holder.appendChild(err);
      }
      err.textContent = 'Ошибка JSON: ' + message;
    } else if (err) {
      err.textContent = '';
    }
  }

  function formatJson(ta) {
    if (!ta.value.trim()) {
      setState(ta, true, '');
      return;
    }
    try {
      var parsed = JSON.parse(ta.value);
      ta.value = JSON.stringify(parsed, null, 2);
      setState(ta, true, '');
    } catch (e) {
      setState(ta, false, e.message);
    }
  }

  function validateJson(ta) {
    if (!ta.value.trim()) {
      setState(ta, true, '');
      return;
    }
    try {
      JSON.parse(ta.value);
      setState(ta, true, '');
    } catch (e) {
      setState(ta, false, e.message);
    }
  }

  function init() {
    var fields = document.querySelectorAll('textarea.i18n-json-field');
    for (var i = 0; i < fields.length; i++) {
      (function (ta) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'json-format-btn';
        btn.textContent = 'Форматировать';
        ta.parentElement.insertBefore(btn, ta.nextSibling);
        btn.addEventListener('click', function () { formatJson(ta); });
        ta.addEventListener('blur', function () { validateJson(ta); });
      })(fields[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
