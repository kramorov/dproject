document.addEventListener('DOMContentLoaded', function() {
    console.log("=== PNEUMATIC ACTUATOR SELECTED JS LOADED ===");

    // Функция для обновления опций при выборе модели
    const modelSelector = document.querySelector('.pneumatic-model-selector');
    const optionSelectors = document.querySelectorAll('.pneumatic-option-selector');

    if (modelSelector) {
        modelSelector.addEventListener('change', function() {
            const modelId = this.value;
            updateOptions(modelId);
        });

        // Инициализация при загрузке
        if (modelSelector.value) {
            updateOptions(modelSelector.value);
        }
    }

    // Инициализация генератора описаний
    initDescriptionGenerator();

    function updateOptions(modelId) {
        if (!modelId) {
            // Сброс опций если модель не выбрана
            optionSelectors.forEach(select => {
                select.innerHTML = '<option value="">---------</option>';
            });
            return;
        }

        // URL для получения опций
        const url = `/admin/pneumatic_actuators/get_options/?model_id=${modelId}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                optionSelectors.forEach(select => {
                    const optionType = select.dataset.optionType;
                    const options = data[optionType] || [];

                    // Сохраняем текущее значение
                    const currentValue = select.value;

                    // Обновляем options
                    select.innerHTML = '<option value="">---------</option>';
                    options.forEach(option => {
                        const newOption = new Option(option.name, option.id, false, option.id == currentValue);
                        select.add(newOption);
                    });
                });
            })
            .catch(error => {
                console.error('Error loading options:', error);
            });
    }

    function initDescriptionGenerator() {
        const generateBtn = document.querySelector('.generate-description-btn');
        if (!generateBtn) return;

        generateBtn.addEventListener('click', function() {
            const objectId = this.dataset.objectId;
            const csrfToken = getCsrfToken();

            if (!objectId) {
                alert('Ошибка: ID объекта не найден');
                return;
            }

            // Показываем индикатор загрузки
            const statusDiv = document.querySelector('.description-status');
            statusDiv.innerHTML = '<span class="loading">⏳ Генерация описания...</span>';
            generateBtn.disabled = true;

            // Отправляем запрос на генерацию
            fetch(`/admin/pneumatic_actuators/pneumaticactuatorselected/${objectId}/generate-description/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Обновляем предпросмотр
                    const previewDiv = document.querySelector('.description-preview pre');
                    if (previewDiv) {
                        const previewText = data.description.length > 500
                            ? data.description.substring(0, 500) + '...'
                            : data.description;
                        previewDiv.textContent = previewText;
                    }

                    // Обновляем поле описания (если оно видимо)
                    const descriptionField = document.querySelector('#id_description');
                    if (descriptionField) {
                        descriptionField.value = data.description;
                    }

                    statusDiv.innerHTML = '<span class="success">✅ Описание успешно сгенерировано!</span>';

                    // Автоматически обновляем страницу через 2 секунды
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                } else {
                    statusDiv.innerHTML = `<span class="error">❌ Ошибка: ${data.message}</span>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                statusDiv.innerHTML = '<span class="error">❌ Ошибка при генерации описания</span>';
            })
            .finally(() => {
                generateBtn.disabled = false;
            });
        });
    }

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

    // Автоматическая генерация при изменении опций (опционально)
    const autoGenerateCheckbox = document.getElementById('id_auto_generate');
    if (autoGenerateCheckbox && autoGenerateCheckbox.checked) {
        const optionFields = document.querySelectorAll('select[name^="selected_"]');
        optionFields.forEach(field => {
            field.addEventListener('change', function() {
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
});