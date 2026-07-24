document.addEventListener('DOMContentLoaded', function () {
    console.log("=== PNEUMATIC ACTUATOR ADMIN LOADED ===");

    const modelSelect = document.getElementById('id_selected_model');
    const apiUrl = '/api/pneumatic_actuators/api/options/';

    const fieldMapping = {
        'selected_safety_position': 'safety_positions',
        'selected_springs_qty': 'springs_qty',
        'selected_temperature': 'temperature_options',
        'selected_ip': 'ip_options',
        'selected_exd': 'exd_options',
        'selected_body_coating': 'coating_options'
    };

    if (modelSelect) {
        modelSelect.addEventListener('change', function () {
            const modelId = this.value;
            console.log("Model changed to:", modelId);

            if (modelId) {
                updateAllOptions(modelId);
            } else {
                clearAllOptions();
            }
        });

        if (modelSelect.value) {
            console.log("Initial load for model:", modelSelect.value);
            updateAllOptions(modelSelect.value);
        }
    }

    async function updateAllOptions(modelId) {
        try {
            const response = await fetch(`${apiUrl}?model_id=${modelId}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("API response:", data);

            Object.keys(fieldMapping).forEach(fieldName => {
                const selectElement = document.getElementById(`id_${fieldName}`);
                const optionsKey = fieldMapping[fieldName];
                const options = data[optionsKey] || [];

                updateFieldVisibility(fieldName, selectElement, options);
            });

        } catch (error) {
            console.error('Failed to load options:', error);
            clearAllOptions();
        }
    }

    function updateFieldVisibility(fieldName, selectElement, options) {
        if (!selectElement) {
            console.log(`Select element not found for: ${fieldName}`);
            return;
        }

        // НАХОДИМ КОНТЕЙНЕР ПОЛЯ - несколько способов
        let fieldContainer = null;
        let methodUsed = 'none';

        // Способ 1: Ищем по классу field-{field_name}
        fieldContainer = document.querySelector(`.field-${fieldName}`);
        if (fieldContainer) {
            methodUsed = 'CSS class field-{name}';
            console.log(`🔍 Found container for ${fieldName} via ${methodUsed}`);
        }

        // Способ 2: Ищем родительский div с классом field-box или form-row
        if (!fieldContainer) {
            let parent = selectElement.parentElement;
            let depth = 0;
            while (parent && depth < 10) { // ограничиваем глубину поиска
                if (parent.classList && (
                    parent.classList.contains('field-box') ||
                    parent.classList.contains('form-row') ||
                    parent.classList.contains('field')
                )) {
                    fieldContainer = parent;
                    methodUsed = `parent traversal (${depth} levels) - class: ${Array.from(parent.classList).join(', ')}`;
                    console.log(`🔍 Found container for ${fieldName} via ${methodUsed}`);
                    break;
                }
                parent = parent.parentElement;
                depth++;
            }
            if (!fieldContainer && depth >= 10) {
                console.log(`🔍 Container for ${fieldName} not found in 10 parent levels`);
            }
        }

        // Способ 3: Ищем по label
        if (!fieldContainer) {
            const label = document.querySelector(`label[for="id_${fieldName}"]`);
            if (label) {
                fieldContainer = label.closest('.field-box') || label.closest('.form-row') || label.parentElement;
                if (fieldContainer) {
                    methodUsed = 'label association';
                    console.log(`🔍 Found container for ${fieldName} via ${methodUsed}`);
                }
            }
        }

        // Способ 4: Ищем по data-атрибуту или другим признакам
        if (!fieldContainer) {
            // Ищем любой элемент с data-field-name атрибутом
            fieldContainer = document.querySelector(`[data-field-name="${fieldName}"]`);
            if (fieldContainer) {
                methodUsed = 'data-field-name attribute';
                console.log(`🔍 Found container for ${fieldName} via ${methodUsed}`);
            }
        }

        console.log(`📊 Field: ${fieldName}, Container: ${fieldContainer ? 'FOUND' : 'NOT FOUND'}, Method: ${methodUsed}, Options: ${options.length}`);

        // Логируем структуру DOM для отладки
        if (!fieldContainer) {
            console.log(`🔄 DOM structure for ${fieldName}:`);
            let element = selectElement;
            let level = 0;
            while (element && level < 6) {
                const classes = element.className ? ` classes: ${element.className}` : '';
                const id = element.id ? ` id: ${element.id}` : '';
                console.log(`  ${'  '.repeat(level)}${element.tagName}${id}${classes}`);
                element = element.parentElement;
                level++;
            }
        }

        // Управляем видимостью
        if (options.length === 0) {
            // Скрываем поле если нет опций
            if (fieldContainer) {
                fieldContainer.style.display = 'none';
                console.log(`✅ HIDING field: ${fieldName} using container`);
            } else {
                console.log(`❌ Cannot hide ${fieldName} - container not found, trying direct approach`);
                // Прячем сам select и его label
                selectElement.style.display = 'none';
                selectElement.style.visibility = 'hidden';

                const label = document.querySelector(`label[for="id_${fieldName}"]`);
                if (label) {
                    label.style.display = 'none';
                    label.style.visibility = 'hidden';
                }

                // Прячем возможные контейнеры
                const possibleContainers = [
                    selectElement.closest('div'),
                    selectElement.parentElement,
                    document.querySelector(`.field-${fieldName}`)
                ];

                possibleContainers.forEach(container => {
                    if (container && container.style) {
                        container.style.display = 'none';
                    }
                });

                console.log(`⚠️  HIDING field: ${fieldName} using direct element hiding`);
            }

            // Очищаем значение
            selectElement.innerHTML = '<option value="">---------</option>';
            selectElement.value = '';
        } else {
            // Показываем поле если есть опции
            if (fieldContainer) {
                fieldContainer.style.display = 'block';
                fieldContainer.style.visibility = 'visible';
                console.log(`✅ SHOWING field: ${fieldName} using container`);
            } else {
                console.log(`❌ Cannot show ${fieldName} - container not found, trying direct approach`);
                // Показываем сам select и его label
                selectElement.style.display = 'block';
                selectElement.style.visibility = 'visible';

                const label = document.querySelector(`label[for="id_${fieldName}"]`);
                if (label) {
                    label.style.display = 'block';
                    label.style.visibility = 'visible';
                }

                console.log(`⚠️  SHOWING field: ${fieldName} using direct element showing`);
            }

            // Обновляем опции (если нужно)
            updateSelectOptions(selectElement, options);
        }
    }

    function updateSelectOptions(selectElement, options) {
        const currentValue = selectElement.value;

        selectElement.innerHTML = '<option value="">---------</option>';
        options.forEach(option => {
            const displayText = option.encoding ?
                `${option.name} (${option.encoding})` : option.name;
            const optionElement = new Option(displayText, option.id);

            if (option.is_default) {
                optionElement.selected = true;
            }

            selectElement.add(optionElement);
        });

        if (currentValue && options.find(opt => opt.id == currentValue)) {
            selectElement.value = currentValue;
        }
    }

    function clearAllOptions() {
        Object.keys(fieldMapping).forEach(fieldName => {
            const selectElement = document.getElementById(`id_${fieldName}`);
            if (selectElement) {
                selectElement.innerHTML = '<option value="">---------</option>';
                selectElement.value = '';
            }
        });
    }

    // ДОПОЛНИТЕЛЬНО: Добавим диагностику структуры DOM
    console.log("=== DOM STRUCTURE DEBUG ===");
    Object.keys(fieldMapping).forEach(fieldName => {
        const selectElement = document.getElementById(`id_${fieldName}`);
        if (selectElement) {
            console.log(`Field ${fieldName}:`, selectElement);
            console.log(`Parent structure:`, selectElement.parentElement?.className, selectElement.parentElement?.parentElement?.className);
        }
    });
});