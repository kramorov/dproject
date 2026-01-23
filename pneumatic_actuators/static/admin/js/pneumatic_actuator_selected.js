document.addEventListener('DOMContentLoaded', function () {
    console.log("=== PNEUMATIC ACTUATOR SELECTED JS LOADED В10===");

    // Показываем все скрытые контейнеры полей опций
    const hiddenFieldContainers = document.querySelectorAll('[class*="field-selected_"]');
    hiddenFieldContainers.forEach(container => {
        const style = window.getComputedStyle(container);
        if (style.display === 'none') {
            console.log(`Showing hidden field container:`, container.className);
            container.style.display = 'flex';
        }
    });

    // Также показываем любые другие скрытые элементы с data-context
    const hiddenContextFields = document.querySelectorAll('[data-context]');
    hiddenContextFields.forEach(field => {
        let parent = field.parentElement;
        while (parent) {
            const style = window.getComputedStyle(parent);
            if (style.display === 'none') {
                parent.style.display = '';
            }
            parent = parent.parentElement;
        }
    });

    // 1. Находим селектор модели
    const modelSelector = document.querySelector('select[name="selected_model_line_item"]');
    console.log("Model selector found:", !!modelSelector);
    if (modelSelector) {
        console.log("Model selector value:", modelSelector.value);
    }

    // 2. Находим ВСЕ селекторы опций (кроме модели)
    const allSelects = document.querySelectorAll('select');
    const optionSelectors = Array.from(allSelects).filter(select =>
        select.name !== 'selected_model_line_item' &&
        select.name.startsWith('selected_')
    );

    console.log("Found option selectors:", optionSelectors.length);
    optionSelectors.forEach((select, i) => {
        console.log(`  ${i}: name="${select.name}", id="${select.id}", current value="${select.value}"`);
    });

    // 3. Карта соответствия имен полей и ключей из API
    const fieldToApiKeyMap = {
        'selected_safety_position': 'safety_positions',
        'selected_springs_qty': 'springs_qty',
        'selected_temperature': 'temperature_options',
        'selected_ip': 'ip_options',
        'selected_exd': 'exd_options',
        'selected_body_coating': 'body_coating_options',
        'selected_hand_wheel': 'hand_wheel_options' // если есть в API
    };

    // 4. Функция обновления опций
    function updateOptions(modelId) {
        console.log("=== updateOptions called with modelId:", modelId);

        if (!modelId) {
            console.warn("No model ID provided, clearing options");
            optionSelectors.forEach(select => {
                select.innerHTML = '<option value="">---------</option>';
                // Если используется Select2
                if (typeof jQuery !== 'undefined' && $(select).hasClass('select2-hidden-accessible')) {
                    $(select).trigger('change.select2');
                }
            });
            return;
        }

        const url = `/api/pneumatic_actuators/options/?model_id=${modelId}`;
        console.log("Fetching options from:", url);

        fetch(url)
            .then(response => {
                console.log("Response status:", response.status);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("API response received, keys:", Object.keys(data));

                // Проверяем наличие данных для каждого поля
                for (const [fieldName, apiKey] of Object.entries(fieldToApiKeyMap)) {
                    console.log(`${fieldName} -> ${apiKey}:`, data[apiKey] ? data[apiKey].length + ' items' : 'not found');
                }

                // Обновляем каждый селектор опций
                optionSelectors.forEach(select => {
                    const fieldName = select.name;
                    const apiKey = fieldToApiKeyMap[fieldName];

                    if (!apiKey) {
                        console.warn(`No API key mapping for field: ${fieldName}`);
                        return;
                    }

                    const options = data[apiKey] || [];
                    console.log(`Processing ${fieldName} (${apiKey}): ${options.length} options found`);

                    // Сохраняем текущее значение
                    const currentValue = select.value;
                    console.log(`  Current value: ${currentValue}`);

                    // Очищаем селектор (кроме первого пустого option если есть)
                    const hasEmptyOption = select.options.length > 0 && select.options[0].value === "";
                    select.innerHTML = hasEmptyOption ? '<option value="">---------</option>' : '';

                    if (options.length === 0) {
                        console.warn(`  No options available for ${fieldName}`);
                        if (!hasEmptyOption) {
                            select.innerHTML = '<option value="">---------</option>';
                        }
                        return;
                    }

                    // Фильтруем дубликаты по ID
                    const seenIds = new Set();
                    const uniqueOptions = [];

                    options.forEach(option => {
                        if (option.id && !seenIds.has(option.id)) {
                            seenIds.add(option.id);
                            uniqueOptions.push(option);
                        }
                    });

                    console.log(`  After deduplication: ${uniqueOptions.length} unique options`);

                    // Добавляем опции
                    uniqueOptions.forEach(option => {
                        const displayText = option.name || option.encoding || `ID: ${option.id}`;

                        // ВАЖНО: сравниваем как числа, так как ID - числа
                        const isSelected = parseInt(option.id) === parseInt(currentValue);

                        if (isSelected) {
                            console.log(`    Will select: ${option.id} (${displayText}) - matches current ${currentValue}`);
                        }

                        const newOption = new Option(displayText, option.id, false, isSelected);
                        select.add(newOption);
                    });

                    // Если текущее значение не найдено в новых опциях, сбрасываем
                    if (currentValue) {
                        const currentInt = parseInt(currentValue);
                        const valueExists = Array.from(seenIds).some(id => id === currentInt);

                        if (!valueExists) {
                            console.warn(`  Value ${currentValue} not found in new options. Available:`, Array.from(seenIds));
                            // Только предупреждение, не сбрасываем!
                        } else {
                            console.log(`  Value ${currentValue} exists in new options`);
                        }
                    }

                    // Обновляем Select2 если используется
                    if (typeof jQuery !== 'undefined' && $(select).hasClass('select2-hidden-accessible')) {
                        $(select).trigger('change.select2');
                    }

                    console.log(`  ${fieldName} updated with ${uniqueOptions.length} options`);
                });

                console.log("=== All options updated successfully ===");
            })
            .catch(error => {
                console.error('Error fetching options:', error);
                // Не показываем alert, чтобы не мешать пользователю
            });
    }

    // 5. Инициализация при загрузке страницы
    if (modelSelector && modelSelector.value) {
        console.log("Initializing with model ID:", modelSelector.value);
        // Ждем полной загрузки DOM и возможной инициализации Select2
        setTimeout(() => {
            updateOptions(modelSelector.value);
        }, 800);
    }

    // 6. Обработчик изменения модели
    if (modelSelector) {
        modelSelector.addEventListener('change', function () {
            const newModelId = this.value;
            console.log("=== Model changed to ID:", newModelId);
            updateOptions(newModelId);
        });
    }

    // 7. Инициализация генератора описаний (без изменений)
    function initDescriptionGenerator() {
        const generateBtn = document.querySelector('.generate-description-btn');
        if (!generateBtn) {
            console.log('Кнопка генерации не найдена');
            return;
        }

        console.log('Кнопка генерации найдена, добавляем обработчик');
        generateBtn.addEventListener('click', function () {
            const objectId = this.dataset.objectId;
            const csrfToken = getCsrfToken();

            console.log('Клик по кнопке генерации, objectId:', objectId);

            if (!objectId) {
                alert('Ошибка: ID объекта не найден');
                return;
            }

            // Показываем индикатор загрузки
            const statusDiv = document.querySelector('.description-status');
            if (statusDiv) {
                statusDiv.innerHTML = '<span class="loading">⏳ Генерация описания...</span>';
            }
            generateBtn.disabled = true;
            const originalText = generateBtn.innerHTML;
            generateBtn.innerHTML = '⏳ Генерация...';

            // Отправляем запрос на генерацию
            console.log('Отправка запроса на генерацию...');
            fetch(`/admin/pneumatic_actuators/pneumaticactuatorselected/${objectId}/generate-description/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            })
                .then(response => {
                    console.log('Ответ получен, статус:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Данные получены:', data);
                    if (data.success) {
                        console.log('Генерация успешна, открываем новое окно');
                        // ОТКРЫВАЕМ ОПИСАНИЕ В НОВОМ ОКНЕ
                        openDescriptionInNewWindow(data.description);

                        // Обновляем поле описания (если оно видимо)
                        const descriptionField = document.querySelector('#id_description');
                        if (descriptionField) {
                            descriptionField.value = data.description;
                        }

                        if (statusDiv) {
                            statusDiv.innerHTML = '<span class="success">✅ Описание успешно сгенерировано!</span>';
                        }
                    } else {
                        console.error('Ошибка в данных:', data.message);
                        if (statusDiv) {
                            statusDiv.innerHTML = `<span class="error">❌ Ошибка: ${data.message}</span>`;
                        }
                    }
                })
                .catch(error => {
                    console.error('Fetch error:', error);
                    if (statusDiv) {
                        statusDiv.innerHTML = '<span class="error">❌ Ошибка при генерации описания</span>';
                    }
                })
                .finally(() => {
                    console.log('Завершение генерации');
                    generateBtn.disabled = false;
                    generateBtn.innerHTML = originalText;
                });
        });
    }

    // 8. Функция для открытия описания в новом окне (без изменений)
    function openDescriptionInNewWindow(descriptionText) {
        console.log('Открытие нового окна с описанием');

        // Очищаем текст перед обработкой
        const cleanedText = descriptionText
            .replace(/\n{3,}/g, '\n\n')  // Заменяем 3+ переноса на 2
            .replace(/\n{2}/g, '\n');    // Заменяем 2 переноса на 1

        // Функция для экранирования HTML (но НЕ для таблиц)
        function escapeHtml(text) {
            // Разделяем текст на части: HTML таблицы и обычный текст
            const parts = text.split(/(<table[\s\S]*?<\/table>)/);

            return parts.map(part => {
                if (part.startsWith('<table') && part.endsWith('</table>')) {
                    // Это HTML таблица - не экранируем
                    return part;
                } else {
                    // Это обычный текст - экранируем и заменяем переносы строк
                    const div = document.createElement('div');
                    div.textContent = part;
                    return div.innerHTML.replace(/\n/g, '<br>');
                }
            }).join('');
        }

        // Размеры окна
        const width = 1000;
        const height = 700;
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;

        // Параметры окна
        const features = `
            width=${width},
            height=${height},
            left=${left},
            top=${top},
            resizable=yes,
            scrollbars=yes,
            toolbar=no,
            menubar=no,
            location=no,
            status=no
        `.replace(/\s+/g, '');

        // Открываем новое окно
        const newWindow = window.open('', 'Описание пневмопривода', features);

        if (!newWindow) {
            alert('Пожалуйста, разрешите всплывающие окна для этого сайта');
            return;
        }

        // Формируем HTML для нового окна
        newWindow.document.write(`
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Описание пневмопривода</title>
                <style>
                /* Добавьте стили для таблицы */
                .description-content table {
                    border-collapse: collapse;
                    margin: 20px 0;
                    width: 100%;
                    font-size: 13px;
                    font-family: inherit;
                }
                
                .description-content th,
                .description-content td {
                    border: 1px solid #ddd;
                    padding: 8px 12px;
                    text-align: center;
                    min-width: 80px;
                }
                
                .description-content th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
                
                .description-content tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background: #f5f5f5;
                        padding: 20px;
                        overflow-y: auto;
                        min-height: 100vh;
                    }
                    
                    .container {
                        max-width: none;
                        width: 95%;
                        margin: 0 auto;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        padding: 30px;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                    }
                    
                    h1 {
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                        font-size: 24px;
                    }
                    
                    .description-content {
                        white-space: pre-wrap;
                        font-size: 14px;
                        line-height: 1.8;
                        max-height: none;
                        overflow: visible;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    }
                    
                    .description-content p {
                        margin-bottom: 10px;
                    }
                    
                    .description-content table {
                        border-collapse: collapse;
                        margin: 20px 0;
                        width: 100%;
                        font-size: 13px;
                        font-family: inherit;
                    }
                    
                    .description-content th,
                    .description-content td {
                        border: 1px solid #ddd;
                        padding: 8px 12px;
                        text-align: center;
                    }
                    
                    .description-content th {
                        background-color: #f8f9fa;
                        font-weight: bold;
                    }
                    
                    .description-content tr:nth-child(even) {
                        background-color: #f9f9f9;
                    }
                    
                    .controls {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        z-index: 1000;
                        background: white;
                        padding: 10px;
                        border-radius: 6px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                        display: flex;
                        gap: 10px;
                    }
                    
                    .btn {
                        padding: 8px 15px;
                        background: #3498db;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: background 0.3s;
                        white-space: nowrap;
                    }
                    
                    .btn:hover {
                        background: #2980b9;
                    }
                    
                    .btn-copy {
                        background: #2ecc71;
                    }
                    
                    .btn-copy:hover {
                        background: #27ae60;
                    }
                    
                    .btn-print {
                        background: #9b59b6;
                    }
                    
                    .btn-print:hover {
                        background: #8e44ad;
                    }
                    
                    .btn-close {
                        background: #e74c3c;
                    }
                    
                    .btn-close:hover {
                        background: #c0392b;
                    }
                    
                    @media print {
                        .controls {
                            display: none;
                        }
                        
                        body {
                            background: white;
                            padding: 0;
                        }
                        
                        .container {
                            box-shadow: none;
                            padding: 0;
                        }
                    }
                    
                    /* Для длинных таблиц */
                    .description-content pre {
                        overflow-x: auto;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                </style>
            </head>
            <body>
                <div class="controls">
                    <button class="btn btn-copy" id="copy-btn">📋 Копировать</button>
                    <button class="btn btn-print" id="print-btn">🖨️ Печать</button>
                    <button class="btn btn-close" id="close-btn">✖️ Закрыть</button>
                </div>
                
                <div class="container">
                    <h1>Описание пневмопривода</h1>
                    <div class="description-content" id="description-content">
                         ${escapeHtml(cleanedText)}
                    </div>
                </div>
                
                <script>
                    // Функция для копирования в буфер обмена
                    document.getElementById('copy-btn').addEventListener('click', function() {
                        const content = document.getElementById('description-content');
                        const text = content.innerText || content.textContent;
                        
                        navigator.clipboard.writeText(text).then(function() {
                            const btn = this;
                            const originalText = btn.innerHTML;
                            btn.innerHTML = '✅ Скопировано!';
                            btn.style.background = '#27ae60';
                            
                            setTimeout(function() {
                                btn.innerHTML = originalText;
                                btn.style.background = '#2ecc71';
                            }, 2000);
                        }.bind(this)).catch(function(err) {
                            alert('Ошибка при копировании: ' + err);
                        });
                    });
                    
                    // Функция для печати
                    document.getElementById('print-btn').addEventListener('click', function() {
                        window.print();
                    });
                    
                    // Функция для закрытия окна
                    document.getElementById('close-btn').addEventListener('click', function() {
                        window.close();
                    });
                    
                    // Автоматически прокручиваем в начало
                    window.scrollTo(0, 0);
                    
                    // Фокус на контент
                    document.getElementById('description-content').focus();
                </script>
            </body>
            </html>
        `);

        newWindow.document.close();
        newWindow.focus();
        console.log('Новое окно открыто успешно');
    }

    // 9. Функция для получения CSRF токена (без изменений)
    function getCsrfToken() {
        // Получаем CSRF токен из cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 10. Автоматическая генерация при изменении опций (опционально)
    const autoGenerateCheckbox = document.getElementById('id_auto_generate');
    if (autoGenerateCheckbox && autoGenerateCheckbox.checked) {
        const optionFields = document.querySelectorAll('select[name^="selected_"]');
        optionFields.forEach(field => {
            field.addEventListener('change', function () {
                setTimeout(checkAndGenerate, 1000);
            });
        });
    }

    function checkAndGenerate() {
        // Проверяем, все ли обязательные поля заполнены
        // и генерируем описание автоматически
        const generateBtn = document.querySelector('.generate-description-btn');
        if (generateBtn) {
            generateBtn.click();
        }
    }

    // 11. Инициализируем генератор описаний
    initDescriptionGenerator();

    console.log("=== JS initialization complete ===");
});