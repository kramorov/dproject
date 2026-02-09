// features/static/features/js/admin-feature-template.js
(function($) {
    'use strict';

    // Функция для добавления характеристики
    function addFeature() {
        var featureSelect = $('#feature-select');
        var featureId = featureSelect.val();
        var featureOption = featureSelect.find('option:selected');

        if (!featureId) {
            alert('Выберите характеристику из списка');
            return;
        }

        // Проверяем, не добавлена ли уже эта характеристика
        if ($('.feature-item[data-feature-id="' + featureId + '"]').length > 0) {
            alert('Эта характеристика уже добавлена в шаблон');
            return;
        }

        var featureName = featureOption.data('name');
        var featureCode = featureOption.data('code');
        var dataType = featureOption.data('data-type');
        var unit = featureOption.data('unit') || '-';
        var isRequired = featureOption.data('is-required') === 'true';

        // Определяем отображение типа данных
        var dataTypeDisplay = {
            'text': 'Текст',
            'number': 'Число',
            'boolean': 'Да/Нет',
            'select': 'Выбор из списка',
            'range': 'Диапазон',
            'file': 'Файл',
            'link': 'Ссылка'
        }[dataType] || dataType;

        // Определяем порядковый номер
        var order = $('#features-list .feature-item').length + 1;

        // Создаем HTML для новой характеристики
        var html = `
        <div class="feature-item" data-feature-id="${featureId}" 
             style="margin-bottom: 15px; padding: 15px; border: 1px solid #ddd; 
                    border-radius: 5px; background: #f9f9f9;">
            <div style="display: flex; justify-content: space-between; 
                        align-items: center; margin-bottom: 10px;">
                <div>
                    <span style="font-weight: bold;">#${order}. ${featureName}</span>
                    <span style="color: #666; margin-left: 10px;">(${featureCode})</span>
                </div>
                <div>
                    <button type="button" class="button remove-feature-btn" 
                            style="background: #dc3545; color: white;">
                        ❌ Удалить
                    </button>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px;">
                        <strong>Тип данных:</strong> ${dataTypeDisplay}
                    </label>
                    <label style="display: block; margin-bottom: 5px;">
                        <strong>Единица измерения:</strong> ${unit}
                    </label>
                    <label style="display: block; margin-bottom: 5px;">
                        <strong>Обязательно:</strong> ${isRequired ? 'Да' : 'Нет'}
                    </label>
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                        Значение по умолчанию:
                    </label>
                    <textarea class="feature-default-value" 
                              rows="3"
                              style="width: 100%; padding: 8px; border: 1px solid #ccc; 
                                     border-radius: 3px;"></textarea>
                    
                    <div style="margin-top: 10px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                            Порядок:
                        </label>
                        <input type="number" class="feature-order" 
                               value="${order}"
                               style="width: 80px; padding: 5px; border: 1px solid #ccc; 
                                      border-radius: 3px;">
                    </div>
                </div>
            </div>
        </div>
        `;

        // Добавляем характеристику в список
        var featuresList = $('#features-list');
        if (!featuresList.length) {
            featuresList = $('<div id="features-list"></div>');
            $('#features-list-container').html('<h4>Текущие характеристики:</h4>').append(featuresList);
        }
        featuresList.append(html);

        // Очищаем выбор
        featureSelect.val('');

        // Показываем сообщение об успехе
        showStatus('Характеристика добавлена', 'success');

        // Инициализируем обработчик удаления для новой характеристики
        initRemoveFeatureButtons();
    }

    // Функция для удаления характеристики
    function removeFeature(button) {
        if (confirm('Удалить эту характеристику из шаблона?')) {
            $(button).closest('.feature-item').remove();
            reorderFeatures();
            showStatus('Характеристика удалена', 'warning');
        }
    }

    // Функция для перенумерации характеристик
    function reorderFeatures() {
        $('#features-list .feature-item').each(function(index) {
            var orderNumber = index + 1;
            $(this).find('.feature-order').val(orderNumber);
            $(this).find('span:first').text('#' + orderNumber + '. ' +
                $(this).find('span:first').text().replace(/^#\d+\.\s*/, ''));
        });
    }

    // Функция для сохранения характеристик
    function saveFeatures() {
        var templateId = $('#feature-template-editor').data('template-id');
        var features = [];

        $('#features-list .feature-item').each(function() {
            var featureId = $(this).data('feature-id');
            var defaultValue = $(this).find('.feature-default-value').val();
            var order = parseInt($(this).find('.feature-order').val()) || 0;

            features.push({
                type_id: featureId,
                default_value: defaultValue,
                order: order
            });
        });

        // Показываем индикатор загрузки
        var saveBtn = $('#save-features-btn');
        var originalText = saveBtn.text();
        saveBtn.text('⏳ Сохранение...').prop('disabled', true);

        // Отправляем данные на сервер
        $.ajax({
            url: '/admin/features/featuretemplate/save_features/' + templateId + '/',
            type: 'POST',
            data: {
                'features': JSON.stringify(features),
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(data) {
                if (data.success) {
                    showStatus('Характеристики успешно сохранены', 'success');

                    // Обновляем предпросмотр
                    if (data.features_table) {
                        $('#features-table-preview').remove();
                        $('<div id="features-table-preview">' +
                          data.features_table + '</div>').insertAfter('#save-status');
                    }
                } else {
                    showStatus('Ошибка: ' + data.error, 'danger');
                }
            },
            error: function() {
                showStatus('Ошибка при сохранении', 'danger');
            },
            complete: function() {
                saveBtn.text(originalText).prop('disabled', false);
            }
        });
    }

    // Функция для отображения статуса
    function showStatus(message, type) {
        var colors = {
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        };

        var statusDiv = $('#save-status');
        statusDiv.html('<div style="padding: 10px; background: ' + colors[type] +
                      '; color: white; border-radius: 3px;">' + message + '</div>')
                  .show();

        setTimeout(function() {
            statusDiv.fadeOut();
        }, 3000);
    }

    // Функция для инициализации кнопок удаления
    function initRemoveFeatureButtons() {
        $('.remove-feature-btn').off('click').on('click', function() {
            removeFeature(this);
        });
    }

    // Функция для загрузки характеристик типа оборудования
    function loadEquipmentTypeFeatures() {
        var equipmentTypeId = $('#id_equipment_type').val();
        if (!equipmentTypeId) return;

        $.ajax({
            url: '/admin/features/featurevariety/get_by_equipment_type/' + equipmentTypeId + '/',
            success: function(data) {
                if (data.success) {
                    var featureSelect = $('#feature-select');
                    featureSelect.empty();
                    featureSelect.append('<option value="">-- Выберите характеристику --</option>');

                    data.features.forEach(function(feature) {
                        featureSelect.append(
                            '<option value="' + feature.id + '" ' +
                            'data-name="' + feature.name + '" ' +
                            'data-code="' + feature.code + '" ' +
                            'data-data-type="' + feature.data_type + '" ' +
                            'data-unit="' + (feature.unit || '') + '" ' +
                            'data-is-required="' + feature.is_required + '">' +
                            feature.name + ' (' + feature.code + ') - ' +
                            feature.data_type_display + '</option>'
                        );
                    });
                }
            }
        });
    }

    // Инициализация при загрузке страницы
    $(document).ready(function() {
        // Инициализируем кнопки
        $('#add-feature-btn').on('click', addFeature);
        $('#save-features-btn').on('click', saveFeatures);
        initRemoveFeatureButtons();

        // Загружаем характеристики при изменении типа оборудования
        $('#id_equipment_type').on('change', loadEquipmentTypeFeatures);

        // Инициализируем drag and drop для изменения порядка
        if ($('#features-list').length) {
            $('#features-list').sortable({
                handle: '.feature-item',
                axis: 'y',
                update: function(event, ui) {
                    reorderFeatures();
                }
            });
        }

        // Быстрое добавление при двойном клике на опцию
        $('#feature-select').on('dblclick', 'option', function() {
            if ($(this).val()) {
                $('#feature-select').val($(this).val());
                addFeature();
            }
        });

        // Подсветка обязательных полей
        $('label[for="id_name"]').append('<span style="color: red; margin-left: 3px;">*</span>');
        $('label[for="id_code"]').append('<span style="color: red; margin-left: 3px;">*</span>');
        $('label[for="id_equipment_type"]').append('<span style="color: red; margin-left: 3px;">*</span>');
    });

})(django.jQuery);