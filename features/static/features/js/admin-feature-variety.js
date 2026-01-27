// features/static/features/js/admin-feature-variety.js
(function($) {
    'use strict';

    // Функция для обновления видимости полей в зависимости от типа данных
    function updateFieldsVisibility() {
        var dataType = $('#id_data_type').val();

        // Скрываем все дополнительные поля
        $('.data-type-field').hide();

        // Показываем нужные поля в зависимости от типа данных
        switch(dataType) {
            case 'select':
                $('#choices-container').show();
                break;
            case 'number':
            case 'range':
                $('#range-container').show();
                $('#validation-container').show();
                break;
            case 'text':
                $('#validation-container').show();
                break;
            case 'boolean':
                // Для boolean показываем поле значения по умолчанию
                $('#id_default_value').parent().show();
                break;
        }

        // Показываем/скрываем поле единиц измерения
        if (['number', 'range'].includes(dataType)) {
            $('.field-unit').show();
        } else {
            $('.field-unit').hide();
        }
    }

    // Функция для фильтрации типов оборудования
    function initEquipmentTypeFilter() {
        var searchInput = $('<input>', {
            type: 'text',
            id: 'equipment-type-filter',
            placeholder: 'Фильтровать типы оборудования...',
            style: 'margin-bottom: 10px; padding: 5px; width: 100%;'
        });

        // Вставляем поле поиска в нужное место
        $('.field-equipment_types').before(searchInput);

        searchInput.on('keyup', function() {
            var searchText = $(this).val().toLowerCase();
            $('#id_equipment_types_to option').each(function() {
                var text = $(this).text().toLowerCase();
                if (text.indexOf(searchText) > -1) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        });
    }

    // Функция для быстрого выбора всех типов оборудования
    function initSelectAllButton() {
        var selectAllBtn = $('<button>', {
            type: 'button',
            class: 'button',
            id: 'select-all-equipment-types',
            text: '📋 Выбрать все активные',
            style: 'margin: 5px 0;'
        });

        var selectNoneBtn = $('<button>', {
            type: 'button',
            class: 'button',
            id: 'select-none-equipment-types',
            text: '🗑️ Очистить все',
            style: 'margin: 5px 5px;'
        });

        selectAllBtn.on('click', function() {
            // Получаем все активные типы оборудования
            $.ajax({
                url: '/admin/features/equipmenttype/get_active_ids/',
                success: function(data) {
                    if (data.success) {
                        // Выбираем все ID
                        $('#id_equipment_types_to option').each(function() {
                            if (data.ids.includes(parseInt($(this).val()))) {
                                $(this).prop('selected', true);
                            }
                        });

                        // Перемещаем выбранные вправо
                        $('#id_equipment_types_add_link').click();
                    }
                }
            });
        });

        selectNoneBtn.on('click', function() {
            // Очищаем все выбранные
            $('#id_equipment_types_to option').each(function() {
                $(this).prop('selected', true);
            });
            $('#id_equipment_types_remove_link').click();
        });

        $('.field-equipment_types').append(selectAllBtn);
        $('.field-equipment_types').append(selectNoneBtn);
    }

    // Функция для предпросмотра вариантов выбора
    function initChoicesPreview() {
        $('#id_choices').on('input', function() {
            var text = $(this).val();
            var lines = text.split('\\n').filter(line => line.trim() !== '');

            // Обновляем предпросмотр
            var preview = $('#choices-preview');
            if (!preview.length) {
                preview = $('<div>', {
                    id: 'choices-preview',
                    style: 'margin-top: 10px; padding: 10px; border: 1px solid #ddd; ' +
                           'background: #f9f9f9; border-radius: 3px;'
                });
                $('#choices-container').append(preview);
            }

            if (lines.length > 0) {
                var html = '<strong>Предпросмотр вариантов:</strong><br>';
                html += '<div style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px;">';
                lines.forEach(function(line, index) {
                    html += '<span style="padding: 2px 8px; background: #007bff; ' +
                            'color: white; border-radius: 3px;">' + line + '</span>';
                });
                html += '</div>';
                preview.html(html).show();
            } else {
                preview.html('<em>Введите варианты для предпросмотра</em>').show();
            }
        });
    }

    // Функция для валидации регулярного выражения
    function initRegexValidator() {
        $('#id_validation_regex').on('blur', function() {
            var regex = $(this).val();
            if (regex) {
                try {
                    new RegExp(regex);
                    $(this).css('border-color', '#28a745');
                } catch (e) {
                    $(this).css('border-color', '#dc3545');
                    alert('Ошибка в регулярном выражении: ' + e.message);
                }
            }
        });
    }

    // Инициализация при загрузке страницы
    $(document).ready(function() {
        updateFieldsVisibility();
        initEquipmentTypeFilter();
        initSelectAllButton();
        initChoicesPreview();
        initRegexValidator();

        // Обновляем видимость при изменении типа данных
        $('#id_data_type').on('change', updateFieldsVisibility);

        // Подсветка обязательных полей
        $('label[for="id_name"]').append('<span style="color: red; margin-left: 3px;">*</span>');
        $('label[for="id_code"]').append('<span style="color: red; margin-left: 3px;">*</span>');
    });

})(django.jQuery);