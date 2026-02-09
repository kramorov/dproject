// static/admin/js/electric_actuator_selected.js

document.addEventListener('DOMContentLoaded', function () {
    console.log("=== ELECTRIC ACTUATOR SELECTED JS LOADED ===");

    // 1. Находим селектор модели
    const modelSelector = document.querySelector('select[name="selected_model_line_item"]');
    console.log("Model selector found:", !!modelSelector);
    if (modelSelector) {
        console.log("Model selector value:", modelSelector.value);
    }

    // 2. Находим селекторы опций
    const optionSelectors = Array.from(document.querySelectorAll('select')).filter(select =>
        select.name !== 'selected_model_line_item' &&
        select.name.startsWith('selected_')
    );

    console.log("Found option selectors:", optionSelectors.length);
    optionSelectors.forEach((select, i) => {
        console.log(`  ${i}: name="${select.name}", value="${select.value}"`);
    });

    // 3. Карта соответствия полей и ключей API
    const fieldToApiKeyMap = {
    'selected_temperature': 'temperature_options',
    'selected_ip': 'ip_options',
    'selected_exd': 'exd_options',
    'selected_body_coating': 'body_coating_options',
    'selected_hand_wheel': 'hand_wheel_options',
    'selected_power_supply': 'power_supply_options'  // ДОБАВЛЕНО
};

    // 4. Функция обновления опций
    function updateOptions(modelId) {
        console.log("=== updateOptions called ===");
        console.log("Model ID:", modelId);

        if (!modelId) {
            console.warn("No model ID, clearing options");
            optionSelectors.forEach(select => {
                select.innerHTML = '<option value="">---------</option>';
            });
            return;
        }

        const url = `/admin/electric_actuators/electricactuatorselected/get_options/?model_id=${modelId}`;
        console.log("Fetching from:", url);

        fetch(url)
            .then(response => {
                console.log("Response status:", response.status);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("API response keys:", Object.keys(data));

                // Обновляем каждый селектор
                optionSelectors.forEach(select => {
                    const fieldName = select.name;
                    const apiKey = fieldToApiKeyMap[fieldName];

                    if (!apiKey) {
                        console.warn(`No API key for: ${fieldName}`);
                        return;
                    }

                    const options = data[apiKey] || [];
                    const currentValue = select.value;

                    console.log(`  ${fieldName}: ${options.length} options, current: ${currentValue}`);

                    // Сохраняем выбранное значение
                    let selectedOption = null;
                    if (currentValue) {
                        selectedOption = options.find(opt =>
                            parseInt(opt.id) === parseInt(currentValue)
                        );
                    }

                    // Очищаем и добавляем опции
                    select.innerHTML = '<option value="">---------</option>';

                    options.forEach(option => {
                        const isSelected = selectedOption && option.id === selectedOption.id;
                        const displayText = option.name || option.encoding || `ID: ${option.id}`;
                        const opt = new Option(displayText, option.id, false, isSelected);
                        select.add(opt);
                    });

                    // Если выбранное значение было в старых опциях, но не в новых,
                    // оставляем его (пользователь мог вручную выбрать)
                    if (currentValue && !selectedOption) {
                        console.log(`  Value ${currentValue} not found in new options, keeping it`);
                    }
                });

                console.log("=== Options updated ===");
            })
            .catch(error => {
                console.error('Error loading options:', error);
                // Можно показать уведомление, но не alert
                showNotification('Ошибка загрузки опций', 'error');
            });
    }

    // 5. Инициализация при загрузке
    if (modelSelector && modelSelector.value) {
        console.log("Initial load with model:", modelSelector.value);
        setTimeout(() => {
            updateOptions(modelSelector.value);
        }, 500);
    }

    // 6. Обработчик изменения модели
    if (modelSelector) {
        modelSelector.addEventListener('change', function () {
            console.log("Model changed to:", this.value);
            updateOptions(this.value);
        });
    }

    // 7. Функция для добавления кнопки генерации описания
    function addGenerateDescriptionButton() {
        console.log("=== Adding generate description button ===");

        // Проверяем, есть ли уже кнопка
        if (document.querySelector('#generate-description-btn')) {
            console.log("Button already exists");
            return;
        }

        // Получаем object_id из URL
        const url = window.location.pathname;
        console.log("Current URL:", url);

        // Паттерны URL:
        // /admin/electric_actuators/electricactuatorselected/123/change/
        // /admin/electric_actuators/electricactuatorselected/add/
        const match = url.match(/electricactuatorselected\/(\d+)\/change\//);
        const objectId = match ? match[1] : null;

        console.log("Extracted object ID:", objectId);

        // Находим поле описания
        const descriptionField = document.querySelector('#id_description');
        if (!descriptionField) {
            console.log("Description field not found");
            return;
        }

        // Находим контейнер поля описания
        const fieldContainer = descriptionField.closest('.field-description');
        if (!fieldContainer) {
            console.log("Field container not found");
            return;
        }

        // Создаем контейнер для кнопки
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'form-row';
        buttonContainer.style.marginBottom = '15px';

        if (objectId) {
            // Кнопка для существующего объекта
            buttonContainer.innerHTML = `
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                        Действия с описанием:
                    </label>
                    <button type="button" 
                            id="generate-description-btn" 
                            class="button"
                            data-object-id="${objectId}"
                            style="background-color: #4CAF50; 
                                   color: white; 
                                   padding: 8px 16px; 
                                   border: none; 
                                   border-radius: 4px; 
                                   cursor: pointer;
                                   font-size: 13px;">
                        🔄 Сгенерировать описание
                    </button>
                    <button type="button" 
                            id="preview-description-btn" 
                            class="button"
                            data-object-id="${objectId}"
                            style="background-color: #2196F3; 
                                   color: white; 
                                   padding: 8px 16px; 
                                   border: none; 
                                   border-radius: 4px; 
                                   cursor: pointer;
                                   font-size: 13px; 
                                   margin-left: 10px;">
                        👁️ Предпросмотр
                    </button>
                    <div id="description-status" 
                         style="margin-top: 10px; 
                                padding: 8px; 
                                border-radius: 4px;
                                display: none;"></div>
                </div>
            `;
        } else {
            // Сообщение для нового объекта
            buttonContainer.innerHTML = `
                <div style="padding: 10px; 
                            background-color: #f8f9fa; 
                            border: 1px solid #ddd; 
                            border-radius: 4px;">
                    <span style="color: #666;">
                        ⚠️ Сначала сохраните объект, чтобы сгенерировать описание
                    </span>
                </div>
            `;
        }

        // Вставляем кнопку перед полем описания
        fieldContainer.parentNode.insertBefore(buttonContainer, fieldContainer);

        // Инициализируем обработчики кнопок
        initGenerateButton();
        initPreviewButton();
    }

    // 8. Функция инициализации кнопки генерации
    function initGenerateButton() {
        const generateBtn = document.querySelector('#generate-description-btn');
        if (!generateBtn) return;

        generateBtn.addEventListener('click', function() {
            const objectId = this.dataset.objectId;
            console.log("Generate description for:", objectId);

            if (!objectId) {
                showNotification('ID объекта не найден', 'error');
                return;
            }

            // Показываем индикатор
            const statusDiv = document.querySelector('#description-status');
            if (statusDiv) {
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = '<span style="color: #2196F3;">⏳ Генерация описания...</span>';
            }

            generateBtn.disabled = true;
            const originalText = generateBtn.innerHTML;
            generateBtn.innerHTML = '⏳ Генерация...';

            // Получаем CSRF токен
            const csrfToken = getCsrfToken();

            // Отправляем запрос
            fetch(`/admin/electric_actuators/electricactuatorselected/${objectId}/generate-description/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Generate response:", data);

                if (data.success) {
                    // Обновляем поле описания
                    const descriptionField = document.querySelector('#id_description');
                    if (descriptionField) {
                        descriptionField.value = data.description;
                    }

                    // Показываем успех
                    if (statusDiv) {
                        statusDiv.innerHTML = '<span style="color: #4CAF50;">✅ Описание сгенерировано!</span>';
                    }

                    // Автоматически показываем предпросмотр
                    setTimeout(() => {
                        previewDescription(objectId, data.description);
                    }, 1000);

                } else {
                    // Показываем ошибку
                    if (statusDiv) {
                        statusDiv.innerHTML = `<span style="color: #f44336;">❌ ${data.message || 'Ошибка'}</span>`;
                    }
                    showNotification(data.message || 'Ошибка генерации', 'error');
                }
            })
            .catch(error => {
                console.error('Generate error:', error);
                if (statusDiv) {
                    statusDiv.innerHTML = '<span style="color: #f44336;">❌ Ошибка сети</span>';
                }
                showNotification('Ошибка сети при генерации', 'error');
            })
            .finally(() => {
                generateBtn.disabled = false;
                generateBtn.innerHTML = originalText;

                // Скрываем статус через 5 секунд
                if (statusDiv) {
                    setTimeout(() => {
                        statusDiv.style.display = 'none';
                    }, 5000);
                }
            });
        });
    }

    // 9. Функция инициализации кнопки предпросмотра
    function initPreviewButton() {
        const previewBtn = document.querySelector('#preview-description-btn');
        if (!previewBtn) return;

        previewBtn.addEventListener('click', function() {
            const objectId = this.dataset.objectId;
            const descriptionField = document.querySelector('#id_description');
            const description = descriptionField ? descriptionField.value : '';

            if (description.trim()) {
                // Используем существующее описание
                previewDescription(objectId, description);
            } else {
                // Сначала генерируем, потом показываем
                showNotification('Сначала сгенерируйте описание', 'info');
                document.querySelector('#generate-description-btn').click();
            }
        });
    }

    // 10. Функция предпросмотра описания
    function previewDescription(objectId, descriptionText) {
        console.log("Preview description for:", objectId);

        if (!descriptionText || !descriptionText.trim()) {
            showNotification('Нет описания для предпросмотра', 'warning');
            return;
        }

        // Очищаем текст
        const cleanedText = descriptionText
            .replace(/\n{3,}/g, '\n\n')
            .replace(/\n{2}/g, '\n');

        // Экранируем HTML
        function escapeHtml(text) {
            const parts = text.split(/(<table[\s\S]*?<\/table>)/);
            return parts.map(part => {
                if (part.startsWith('<table') && part.endsWith('</table>')) {
                    return part;
                } else {
                    const div = document.createElement('div');
                    div.textContent = part;
                    return div.innerHTML.replace(/\n/g, '<br>');
                }
            }).join('');
        }

        // Открываем в новом окне
        const width = 1000;
        const height = 700;
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;

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

        const newWindow = window.open('', 'Описание электропривода', features);

        if (!newWindow) {
            showNotification('Разрешите всплывающие окна', 'warning');
            return;
        }

        newWindow.document.write(`
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Описание электропривода</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background: #f5f5f5;
                        padding: 20px;
                        margin: 0;
                    }
                    .container {
                        max-width: 900px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        padding: 30px;
                    }
                    h1 {
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }
                    .description-content {
                        white-space: pre-wrap;
                        font-size: 14px;
                        line-height: 1.8;
                    }
                    .controls {
                        margin: 20px 0;
                        text-align: right;
                    }
                    .btn {
                        padding: 8px 16px;
                        background: #3498db;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        margin-left: 10px;
                    }
                    .btn:hover {
                        background: #2980b9;
                    }
                    table {
                        border-collapse: collapse;
                        margin: 15px 0;
                        width: 100%;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: center;
                    }
                    th {
                        background-color: #f8f9fa;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Описание электропривода</h1>
                    <div class="controls">
                        <button class="btn" onclick="window.print()">🖨️ Печать</button>
                        <button class="btn" onclick="copyToClipboard()">📋 Копировать</button>
                        <button class="btn" onclick="window.close()">✖️ Закрыть</button>
                    </div>
                    <div class="description-content" id="content">
                        ${escapeHtml(cleanedText)}
                    </div>
                </div>
                <script>
                    function copyToClipboard() {
                        const content = document.getElementById('content');
                        const text = content.innerText || content.textContent;
                        
                        navigator.clipboard.writeText(text).then(() => {
                            alert('Текст скопирован в буфер обмена');
                        }).catch(err => {
                            alert('Ошибка копирования: ' + err);
                        });
                    }
                </script>
            </body>
            </html>
        `);

        newWindow.document.close();
    }

    // 11. Вспомогательные функции
    function getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    function showNotification(message, type = 'info') {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            z-index: 9999;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            animation: slideIn 0.3s ease;
        `;

        const colors = {
            'info': '#2196F3',
            'success': '#4CAF50',
            'warning': '#ff9800',
            'error': '#f44336'
        };

        notification.style.backgroundColor = colors[type] || colors.info;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Удаляем через 5 секунд
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);

        // Добавляем стили анимации
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // 12. Добавляем кнопку с задержкой (после полной загрузки формы)
    setTimeout(() => {
        addGenerateDescriptionButton();
    }, 1000);

    // 13. Также добавляем кнопку при изменении DOM (на случай динамической загрузки)
    const observer = new MutationObserver(() => {
        if (!document.querySelector('#generate-description-btn')) {
            addGenerateDescriptionButton();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    console.log("=== JS initialization complete ===");
});