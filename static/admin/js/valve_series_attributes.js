function updatePredefinedValues(selectElement) {
    var attributeId = selectElement.value;
    var predefinedValueSelect = $(selectElement).closest('.form-row').find('select[id$="-predefined_value"]');

    if (attributeId) {
        // Загружаем значения для выбранного атрибута
        $.ajax({
            url: '/admin/api/eav-attributes/' + attributeId + '/values/',
            type: 'GET',
            success: function(data) {
                predefinedValueSelect.empty();
                predefinedValueSelect.append($('<option></option>').attr('value', '').text('---------'));

                $.each(data.values, function(index, value) {
                    predefinedValueSelect.append($('<option></option>').attr('value', value.id).text(value.display_name));
                });
            }
        });
    } else {
        predefinedValueSelect.empty();
        predefinedValueSelect.append($('<option></option>').attr('value', '').text('---------'));
    }
}

// Инициализация при загрузке страницы
$(document).ready(function() {
    $('select[id$="-attribute"]').each(function() {
        if ($(this).val()) {
            updatePredefinedValues(this);
        }
    });
});