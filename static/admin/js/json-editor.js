// static/admin/js/json-editor.js

document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.querySelector('.json-editor');
    if (!textarea) return;

    // Добавляем кнопки для форматирования
    const container = textarea.closest('.form-row');
    const buttonBar = document.createElement('div');
    buttonBar.style.margin = '10px 0';
    buttonBar.innerHTML = `
        <button type="button" class="button" id="format-json">🔧 Форматировать</button>
        <button type="button" class="button" id="validate-json">✅ Проверить</button>
        <button type="button" class="button" id="add-example">📋 Добавить пример</button>
        <span id="json-status" style="margin-left: 10px;"></span>
    `;

    container.insertBefore(buttonBar, textarea.nextSibling);

    // Форматирование
    document.getElementById('format-json').addEventListener('click', function() {
        try {
            const json = JSON.parse(textarea.value);
            textarea.value = JSON.stringify(json, null, 2);
            showStatus('✅ Отформатировано', 'green');
        } catch (e) {
            showStatus('❌ Ошибка: ' + e.message, 'red');
        }
    });

    // Валидация
    document.getElementById('validate-json').addEventListener('click', function() {
        try {
            const json = JSON.parse(textarea.value);
            if (Array.isArray(json)) {
                let valid = true;
                json.forEach((item, i) => {
                    if (!item.title || !item.value) {
                        valid = false;
                        showStatus(`❌ Ошибка в строке ${i+1}: нужны поля title и value`, 'red');
                    }
                });
                if (valid) showStatus('✅ JSON корректен', 'green');
            } else {
                showStatus('❌ Должен быть массив', 'red');
            }
        } catch (e) {
            showStatus('❌ Ошибка: ' + e.message, 'red');
        }
    });

    // Добавить пример
    document.getElementById('add-example').addEventListener('click', function() {
        const example = [
            {"title": "Питание блока управления от питания привода", "value": "нет"},
            {"title": "Питание блока управления отдельно от питания привода", "value": "да"},
            {"title": "Селектор Местное/Удаленное управление", "value": "нет"},
            {"title": "Кнопки Открыто/Закрыто/Стоп", "value": "да"}
        ];
        textarea.value = JSON.stringify(example, null, 2);
        showStatus('✅ Пример добавлен', 'green');
    });

    function showStatus(msg, color) {
        const status = document.getElementById('json-status');
        status.textContent = msg;
        status.style.color = color;
        setTimeout(() => {
            status.textContent = '';
        }, 3000);
    }
});