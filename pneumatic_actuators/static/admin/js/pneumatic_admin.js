document.addEventListener('DOMContentLoaded', function() {
    console.log("=== DYNAMIC OPTIONS - API WORKS ===");

    const modelSelect = document.getElementById('id_selected_model');
    const safetySelect = document.getElementById('id_selected_safety_position');
    const springsSelect = document.getElementById('id_selected_springs_qty');

    // Используем рабочий URL
    const apiUrl = '/api/pneumatic_actuators/api/options/';

    if (modelSelect) {
        modelSelect.addEventListener('change', function() {
            const modelId = this.value;
            console.log("Model changed to:", modelId);

            if (modelId) {
                loadOptions(modelId);
            } else {
                clearOptions();
            }
        });

        // При загрузке страницы загружаем опции если модель выбрана
        if (modelSelect.value) {
            console.log("Initial load for model:", modelSelect.value);
            loadOptions(modelSelect.value);
        }
    }

    async function loadOptions(modelId) {
        console.log("Loading options for model:", modelId);

        try {
            const response = await fetch(`${apiUrl}?model_id=${modelId}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("API response:", data);

            // Обновляем списки опций
            updateSelect(safetySelect, data.safety_positions || []);
            updateSelect(springsSelect, data.springs_qty || []);

        } catch (error) {
            console.error('Failed to load options:', error);
            clearOptions();
        }
    }

    function updateSelect(select, options) {
        if (!select) return;

        console.log(`Updating ${select.id} with ${options.length} options`);

        // Сохраняем текущее значение перед обновлением
        const currentValue = select.value;

        // Очищаем и добавляем новые options
        select.innerHTML = '<option value="">---------</option>';

        options.forEach(option => {
            const text = `${option.name} (${option.encoding})`;
            const optionElement = new Option(text, option.id);
            select.add(optionElement);
        });

        // Восстанавливаем значение если оно есть в новых options
        if (currentValue && options.find(opt => opt.id == currentValue)) {
            select.value = currentValue;
            console.log(`Restored value ${currentValue} for ${select.id}`);
        }
    }

    function clearOptions() {
        if (safetySelect) {
            safetySelect.innerHTML = '<option value="">---------</option>';
            safetySelect.value = '';
        }
        if (springsSelect) {
            springsSelect.innerHTML = '<option value="">---------</option>';
            springsSelect.value = '';
        }
    }
});