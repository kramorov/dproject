// static/admin/js/electric_actuator_selected.js

document.addEventListener('DOMContentLoaded', function () {
    console.log("=== ELECTRIC ACTUATOR SELECTED JS LOADED V3 ==");

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
        'selected_safety_position': 'temperature_options',
        'selected_temperature': 'temperature_options',
        'selected_ip': 'ip_options',
        'selected_exd': 'exd_options',
        'selected_body_coating': 'body_coating_options',
        'selected_turn_angle_option': 'turn_angle_option_options',
        'selected_hand_wheel': 'hand_wheel_options',
        'selected_mechanical_indicator_option': 'mechanical_indicator_option_options',
        'selected_blinker_option': 'blinker_option_options',
        'selected_power_supply': 'power_supply_options',
        'selected_control_unit_option': 'control_unit_option_options',
        'selected_body_color_option': 'body_color_option_options',
        'selected_end_switches_option': 'end_switches_option_options',
        'selected_way_switches_option': 'way_switches_option_options',
        'selected_torque_switches_option': 'torque_switches_option_options',
    };

    // 4. Функция для получения доступных опций блоков управления
    async function getAvailableControlsForPowerSupply(powerSupplyId) {
        console.log("Getting available controls for power supply:", powerSupplyId);

        if (!powerSupplyId) {
            return [];
        }

        try {
            const response = await fetch(
                `/admin/electric_actuators/electricactuatorselected/get_available_control_options/?power_supply_id=${powerSupplyId}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log("Control unit options data:", data);

            return data.options || [];
        } catch (error) {
            console.error('Error fetching control unit options:', error);
            return [];
        }
    }

    // 5. Функция фильтрации блоков управления
    async function filterControlUnits(powerSupplyId, forceSelectFirst = false) {
        console.log("=== filterControlUnits ===");
        console.log("Power supply ID:", powerSupplyId);

        const controlSelector = document.querySelector('select[name="selected_control_unit_option"]');
        if (!controlSelector) {
            console.log("Control selector not found");
            return;
        }

        const currentValue = controlSelector.value;
        console.log("Current control option:", currentValue);

        if (!powerSupplyId) {
            console.log("No power supply selected, clearing control unit options");
            controlSelector.innerHTML = '<option value="">---------</option>';
            return;
        }

        const options = await getAvailableControlsForPowerSupply(powerSupplyId);
        console.log("Available control unit options:", options);

        const currentOption = options.find(opt =>
            parseInt(opt.id) === parseInt(currentValue)
        );

        controlSelector.innerHTML = '<option value="">---------</option>';

        let defaultOptionId = null;

        options.forEach(option => {
            const isSelected = currentOption && option.id === currentOption.id;
            const displayText = option.control_unit_name
                ? `${option.control_unit_name} (${option.encoding || 'без кода'})`
                : option.name || option.encoding || `ID: ${option.id}`;

            const opt = new Option(displayText, option.id, false, isSelected);
            controlSelector.add(opt);

            if (option.is_default && !defaultOptionId) {
                defaultOptionId = option.id;
            }
        });

        if (forceSelectFirst && !controlSelector.value && options.length > 0) {
            if (defaultOptionId) {
                controlSelector.value = defaultOptionId;
                console.log("Auto-selected default option:", defaultOptionId);
            } else {
                controlSelector.value = options[0].id;
                console.log("Auto-selected first option:", options[0].id);
            }
        }

        console.log("Final control value:", controlSelector.value);
    }

    // 6. Функция обновления всех опций
    async function updateOptions(modelId) {
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

        try {
            const response = await fetch(url);
            console.log("Response status:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log("API response keys:", Object.keys(data));

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

                let selectedOption = null;
                if (currentValue) {
                    selectedOption = options.find(opt =>
                        parseInt(opt.id) === parseInt(currentValue)
                    );
                }

                select.innerHTML = '<option value="">---------</option>';

                options.forEach(option => {
                    const isSelected = selectedOption && option.id === selectedOption.id;
                    let displayText;

                    if (fieldName === 'selected_control_unit_option') {
                        displayText = option.control_unit_name
                            ? `${option.control_unit_name} (${option.encoding || 'без кода'})`
                            : option.name || option.encoding || `ID: ${option.id}`;
                    } else {
                        displayText = option.name || option.encoding || `ID: ${option.id}`;
                    }

                    const opt = new Option(displayText, option.id, false, isSelected);
                    select.add(opt);
                });

                if (currentValue && !selectedOption) {
                    console.log(`  Value ${currentValue} not found in new options, keeping it`);
                    const oldOption = new Option(`[СТАРОЕ] ID: ${currentValue}`, currentValue, true, true);
                    select.add(oldOption);
                }
            });

            console.log("=== Options updated ===");

            const powerSupplySelector = document.querySelector('select[name="selected_power_supply"]');
            if (powerSupplySelector && powerSupplySelector.value) {
                console.log("Options updated: filtering controls for power supply");
                await filterControlUnits(powerSupplySelector.value);
            }

        } catch (error) {
            console.error('Error loading options:', error);
            showNotification('Ошибка загрузки опций', 'error');
        }
    }

    // 7. Инициализация при загрузке
    if (modelSelector && modelSelector.value) {
        console.log("Initial load with model:", modelSelector.value);
        setTimeout(async () => {
            await updateOptions(modelSelector.value);
        }, 500);
    }

    // 8. Обработчик изменения модели
    if (modelSelector) {
        modelSelector.addEventListener('change', async function () {
            console.log("Model changed to:", this.value);

            const powerSupplySelector = document.querySelector('select[name="selected_power_supply"]');
            const controlSelector = document.querySelector('select[name="selected_control_unit_option"]');

            if (powerSupplySelector) powerSupplySelector.value = '';
            if (controlSelector) controlSelector.innerHTML = '<option value="">---------</option>';

            await updateOptions(this.value);
        });
    }

    // 9. Обработчик изменения напряжения
    const powerSupplySelector = document.querySelector('select[name="selected_power_supply"]');
    if (powerSupplySelector) {
        if (!powerSupplySelector.hasAttribute('data-control-filter-added')) {
            powerSupplySelector.setAttribute('data-control-filter-added', 'true');
            powerSupplySelector.addEventListener('change', async function () {
                console.log("Power supply changed to:", this.value);

                const controlSelector = document.querySelector('select[name="selected_control_unit_option"]');
                if (controlSelector) controlSelector.innerHTML = '<option value="">---------</option>';

                await filterControlUnits(this.value, true);
            });
        }
    }

    // 10. Обработчик изменения блока управления
    const controlUnitSelector = document.querySelector('select[name="selected_control_unit_option"]');
    if (controlUnitSelector) {
        controlUnitSelector.addEventListener('change', function () {
            console.log("Control unit option changed to:", this.value);
        });
    }

    // 11. Функция для добавления кнопок описания
    function addDescriptionButtons() {
        console.log("=== Adding description buttons ===");

        if (document.querySelector('#description-buttons-container')) {
            console.log("Description buttons already exist");
            return;
        }

        const url = window.location.pathname;
        console.log("Current URL:", url);

        const match = url.match(/electricactuatorselected\/(\d+)\/change\//);
        const objectId = match ? match[1] : null;

        console.log("Extracted object ID:", objectId);

        const descriptionField = document.querySelector('#id_description');
        if (!descriptionField) {
            console.log("Description field not found");
            return;
        }

        const fieldContainer = descriptionField.closest('.field-description');
        if (!fieldContainer) {
            console.log("Field container not found");
            return;
        }

        const buttonContainer = document.createElement('div');
        buttonContainer.id = 'description-buttons-container';
        buttonContainer.className = 'form-row';
        buttonContainer.style.marginBottom = '15px';

        if (objectId) {
            buttonContainer.innerHTML = `
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                        Действия с описанием:
                    </label>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
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
                                       font-size: 13px;
                                       display: inline-flex;
                                       align-items: center;
                                       gap: 5px;">
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
                                       display: inline-flex;
                                       align-items: center;
                                       gap: 5px;">
                            👁️ Предпросмотр
                        </button>
                        <button type="button" 
                                id="show-description-btn" 
                                class="button"
                                data-object-id="${objectId}"
                                style="background-color: #9C27B0; 
                                       color: white; 
                                       padding: 8px 16px; 
                                       border: none; 
                                       border-radius: 4px; 
                                       cursor: pointer;
                                       font-size: 13px;
                                       display: inline-flex;
                                       align-items: center;
                                       gap: 5px;">
                            📄 Показать описание
                        </button>
                        <a href="/api/electric_actuators/description/${objectId}/docx/" 
                           class="button"
                           target="_blank"
                           style="background-color: #FF9800; 
                                  color: white; 
                                  padding: 8px 16px; 
                                  border: none; 
                                  border-radius: 4px; 
                                  cursor: pointer;
                                  font-size: 13px;
                                  text-decoration: none;
                                  display: inline-flex;
                                  align-items: center;
                                  gap: 5px;">
                            📥 Скачать Word
                        </a>
                    </div>
                    <div id="description-status" 
                         style="margin-top: 10px; 
                                padding: 8px; 
                                border-radius: 4px;
                                display: none;"></div>
                </div>
            `;
        } else {
            buttonContainer.innerHTML = `
                <div style="padding: 10px; 
                            background-color: #f8f9fa; 
                            border: 1px solid #ddd; 
                            border-radius: 4px;">
                    <span style="color: #666;">
                        ⚠️ Сначала сохраните объект, чтобы работать с описанием
                    </span>
                </div>
            `;
        }

        fieldContainer.parentNode.insertBefore(buttonContainer, fieldContainer);

        initGenerateButton();
        initPreviewButton();
        initShowDescriptionButton();
    }

    // 12. Функция инициализации кнопки генерации
    function initGenerateButton() {
        const generateBtn = document.querySelector('#generate-description-btn');
        if (!generateBtn) return;

        generateBtn.addEventListener('click', function () {
            const objectId = this.dataset.objectId;
            console.log("Generate description for:", objectId);

            if (!objectId) {
                showNotification('ID объекта не найден', 'error');
                return;
            }

            const statusDiv = document.querySelector('#description-status');
            if (statusDiv) {
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = '<span style="color: #2196F3;">⏳ Генерация описания...</span>';
            }

            generateBtn.disabled = true;
            const originalText = generateBtn.innerHTML;
            generateBtn.innerHTML = '⏳ Генерация...';

            const csrfToken = getCsrfToken();

            fetch(`/api/electric_actuators/description/${objectId}/html/`, {
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
                        const descriptionField = document.querySelector('#id_description');
                        if (descriptionField) {
                            descriptionField.value = data.description;
                        }

                        if (statusDiv) {
                            statusDiv.innerHTML = '<span style="color: #4CAF50;">✅ Описание сгенерировано!</span>';
                        }

                        setTimeout(() => {
                            previewDescription(objectId, data.description);
                        }, 1000);

                    } else {
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

                    if (statusDiv) {
                        setTimeout(() => {
                            statusDiv.style.display = 'none';
                        }, 5000);
                    }
                });
        });
    }

    // 13. Функция инициализации кнопки предпросмотра
    function initPreviewButton() {
        const previewBtn = document.querySelector('#preview-description-btn');
        if (!previewBtn) return;

        previewBtn.addEventListener('click', function () {
            const objectId = this.dataset.objectId;
            const descriptionField = document.querySelector('#id_description');
            const description = descriptionField ? descriptionField.value : '';

            if (description.trim()) {
                previewDescription(objectId, description);
            } else {
                showNotification('Сначала сгенерируйте описание', 'info');
                document.querySelector('#generate-description-btn').click();
            }
        });
    }

    // 14. Функция инициализации кнопки показа описания (модальное окно)
    function initShowDescriptionButton() {
        const showBtn = document.querySelector('#show-description-btn');
        if (!showBtn) return;

        showBtn.addEventListener('click', function () {
            const objectId = this.dataset.objectId;
            console.log("Show description for:", objectId);

            if (!objectId) {
                showNotification('ID объекта не найден', 'error');
                return;
            }

            fetch(`/api/electric_actuators/description/${objectId}/html/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("Show description response:", data);

                    if (data.success) {
                        showModal(data.html, objectId);
                    } else {
                        showNotification(data.message || 'Ошибка загрузки', 'error');
                    }
                })
                .catch(error => {
                    console.error('Show description error:', error);
                    showNotification(error.message || 'Ошибка сети при загрузке описания', 'error');
                });
        });
    }

    // 15. Функция показа модального окна
    function showModal(html, instanceId) {
        // Удаляем существующее модальное окно если есть
        const existingModal = document.querySelector('.description-modal');
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.className = 'description-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        const downloadUrl = `/api/electric_actuators/description/${instanceId}/docx/`;
        modal.innerHTML = `
            <div class="modal-content" style="
                background: white;
                padding: 20px;
                border-radius: 8px;
                max-width: 800px;
                max-height: 80vh;
                overflow-y: auto;
                width: 90%;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            ">
                <div class="modal-header" style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #3498db;
                ">
                    <h2 style="margin: 0; color: #2c3e50;">Детальное описание</h2>
                    <div>
                        <a href="/api/electric_actuators/description/${instanceId}/docx/"  
                           class="button" 
                           target="_blank"
                           style="
                                background-color: #FF9800;
                                color: white;
                                padding: 8px 16px;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                                font-size: 13px;
                                text-decoration: none;
                                margin-right: 10px;
                           ">📥 Скачать Word</a>
                        <button class="close-modal button" style="
                            background-color: #dc3545;
                            color: white;
                            padding: 8px 16px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 13px;
                        ">✖ Закрыть</button>
                    </div>
                </div>
                <div class="modal-body" style="
                    max-height: calc(80vh - 100px);
                    overflow-y: auto;
                    padding-right: 10px;
                ">
                    ${html}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.close-modal').addEventListener('click', function () {
            modal.remove();
        });

        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    // 16. Вспомогательные функции
    function getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    function showNotification(message, type = 'info') {
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

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);

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

    function previewDescription(objectId, descriptionText) {
        console.log("Preview description for:", objectId);

        if (!descriptionText || !descriptionText.trim()) {
            showNotification('Нет описания для предпросмотра', 'warning');
            return;
        }

        const cleanedText = descriptionText
            .replace(/\n{3,}/g, '\n\n')
            .replace(/\n{2}/g, '\n');

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
                <\/script>
            </body>
            </html>
        `);

        newWindow.document.close();
    }

    // 17. Добавляем кнопки с задержкой
    setTimeout(() => {
        addDescriptionButtons();
    }, 1000);

    // 18. Observer для динамической загрузки
    const observer = new MutationObserver(() => {
        if (!document.querySelector('#description-buttons-container')) {
            addDescriptionButtons();
        }

        const powerSupplySelector = document.querySelector('select[name="selected_power_supply"]');
        if (powerSupplySelector && !powerSupplySelector.hasAttribute('data-control-filter-added')) {
            powerSupplySelector.setAttribute('data-control-filter-added', 'true');
            powerSupplySelector.addEventListener('change', async function () {
                console.log("Power supply changed (dynamic):", this.value);
                await filterControlUnits(this.value, true);
            });
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    console.log("=== JS initialization complete ===");
});