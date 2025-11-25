document.addEventListener('DOMContentLoaded', function() {
    const modelSelector = document.querySelector('.pneumatic-model-selector');
    const optionSelectors = document.querySelectorAll('.pneumatic-option-selector');
    // console.log("=== PNEUMATIC ACTUATOR JS LOADED ===");
    // alert("JS is working!");  // Убери потом эту строку
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

    function updateOptions(modelId) {
        if (!modelId) {
            // Сброс опций если модель не выбрана
            optionSelectors.forEach(select => {
                select.innerHTML = '<option value="">---------</option>';
            });
            return;
        }

        // URL для получения опций (нужно создать view)
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
            });
    }
});