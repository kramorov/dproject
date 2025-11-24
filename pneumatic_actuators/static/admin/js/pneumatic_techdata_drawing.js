// Кастомные скрипты для админки связей чертежей
document.addEventListener('DOMContentLoaded', function() {
    // Автоматическая подсказка для поля описания
    const descriptionField = document.querySelector('#id_description');
    if (descriptionField) {
        descriptionField.placeholder = 'Введите описание чертежа в контексте этой таблицы данных...';
    }

    // Подсветка уникальных связей
    const tableField = document.querySelector('#id_tech_data_table');
    const drawingField = document.querySelector('#id_drawing');

    if (tableField && drawingField) {
        function checkUniqueCombination() {
            // Здесь можно добавить AJAX проверку на уникальность
        }

        tableField.addEventListener('change', checkUniqueCombination);
        drawingField.addEventListener('change', checkUniqueCombination);
    }
});