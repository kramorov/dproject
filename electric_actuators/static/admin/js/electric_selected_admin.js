/*electric_actuators/static/admin/js/ea_selected_admin.js*/
(function($) {
    $(document).ready(function() {
        // Динамическая фильтрация опций при выборе модели
        $('#id_selected_model_line_item').change(function() {
            var modelLineItemId = $(this).val();

            if (modelLineItemId) {
                // Показываем загрузку
                $('.option-field').prop('disabled', true);

                // Получаем ID model_line через AJAX
                $.ajax({
                    url: '/admin/electric_actuators/api/get_model_line/',
                    data: {
                        'model_line_item_id': modelLineItemId
                    },
                    dataType: 'json',
                    success: function(data) {
                        if (data.success && data.model_line_id) {
                            // Обновляем все поля опций
                            updateOptionFields(data.model_line_id);
                        }
                    },
                    complete: function() {
                        $('.option-field').prop('disabled', false);
                    }
                });
            }
        });

        function updateOptionFields(modelLineId) {
            // Для каждого поля опции делаем AJAX запрос
            $('.option-field').each(function() {
                var field = $(this);
                var fieldName = field.attr('name');

                if (fieldName.startsWith('selected_')) {
                    $.ajax({
                        url: '/admin/electric_actuators/api/get_options/',
                        data: {
                            'model_line_id': modelLineId,
                            'field_name': fieldName
                        },
                        dataType: 'json',
                        success: function(data) {
                            if (data.success) {
                                // Обновляем options
                                var select = field;
                                select.empty();
                                select.append('<option value="">--- Выберите опцию ---</option>');

                                $.each(data.options, function(index, option) {
                                    select.append(
                                        $('<option></option>')
                                            .attr('value', option.id)
                                            .text(option.text)
                                            .prop('selected', option.selected)
                                    );
                                });
                            }
                        }
                    });
                }
            });
        }

        // Кнопка применения дефолтных опций
        $('.apply-defaults-btn').click(function(e) {
            e.preventDefault();

            if (confirm('Применить дефолтные опции из выбранной модели?')) {
                // Добавляем hidden input в форму
                $('<input>').attr({
                    type: 'hidden',
                    name: 'apply_defaults',
                    value: '1'
                }).appendTo('form');

                // Сохраняем форму
                $('form').submit();
            }
        });
    });
})(django.jQuery);