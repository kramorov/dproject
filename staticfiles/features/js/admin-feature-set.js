// features/static/features/js/admin-feature-set.js
(function($) {
    'use strict';

    // Функция для сохранения значений характеристик
    function saveFeatureValues() {
        var featureSetId = $('#feature-set-editor').data('feature-set-id');
        var features = {};

        // Собираем значения со всех полей
        $('.feature-value-item').each(function() {
            var featureId = $(this).data('feature-id');
            var inputType = $(this).find('[name^="feature_"]').attr('type');
            var value = '';

            if (inputType === 'radio') {
                // Для радио-кнопок
                value = $(this).find('[name="feature_' + featureId + '"]:checked').val() || '';
            } else if ($(this).find('select[name="feature_' + featureId + '"]').length) {
                // Для выпадающих списков
                value = $(this).find('select[name="feature_' + featureId + '"]').val() || '';
            } else if ($(this).find('textarea[name="feature_' + featureId + '"]').length) {
                // Для текстовых полей
                value = $(this).find('textarea[name="feature_' + featureId + '"]').val() || '';
            } else {
                // Для input полей
                value = $(this).find('input[name="feature_' + featureId + '"]').val() || '';
            }

            features[featureId] = value;
        });

        // Показываем индикатор загрузки
        var saveBtn = $('#save-feature-values-btn');
        var originalText = saveBtn.text();
        saveBtn.text('⏳ Сохранение...').prop('disabled', true);

        // Отправляем данные на сервер
        $.ajax({
            url: '/admin/features/featureset/save_values/' + featureSetId + '/',
            type: 'POST',
            data: {
                'features': JSON.stringify(features),
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(data) {
                if (data.success) {
                    showStatus('Значения успешно сохранены', 'success');

                    // Обновляем статистику, если есть
                    if (data.stats) {
                        updateStats(data.stats);
                    }

                    // Обновляем предпросмотр
                    if (data.preview_table) {
                        $('.field-preview_table').html(data.preview_table);
                    }
                } else {
                    showStatus('Ошибка: ' + data.error, 'danger');
                }
            },
            error: function(xhr) {
                showStatus('Ошибка при сохранении: ' + xhr.statusText, 'danger');
            },
            complete: function() {
                saveBtn.text(originalText).prop('disabled', false);
            }
        });
    }

    // Функция для сброса к значениям по умолчанию
    function resetToDefaults() {
        if (!confirm('Сбросить все значения к значениям по умолчанию из шаблона?')) {
            return;
        }

        $('.feature-value-item').each(function() {
            var defaultValue = $(this).find('.default-value').text();
            var featureId = $(this).data('feature-id');
            var inputType = $(this).find('[name^="feature_"]').attr('type');

            if (inputType === 'radio') {
                // Сброс радио-кнопок
                $(this).find('[name="feature_' + featureId + '"]').prop('checked', false);
                if (defaultValue) {
                    var radioValue = defaultValue.toLowerCase() === 'true' ? 'true' : 'false';
                    $(this).find('[name="feature_' + featureId + '"][value="' + radioValue + '"]')
                          .prop('checked', true);
                }
            } else if ($(this).find('select[name="feature_' + featureId + '"]').length) {
                // Сброс выпадающих списков
                $(this).find('select[name="feature_' + featureId + '"]').val(defaultValue || '');
            } else if ($(this).find('textarea[name="feature_' + featureId + '"]').length) {
                // Сброс текстовых полей
                $(this).find('textarea[name="feature_' + featureId + '"]').val(defaultValue || '');
            } else {
                // Сброс input полей
                $(this).find('input[name="feature_' + featureId + '"]').val(defaultValue || '');
            }
        });

        showStatus('Значения сброшены к значениям по умолчанию', 'info');
    }

    // Функция для использования значения по умолчанию для одной характеристики
    function useDefaultValue(button) {
        var item = $(button).closest('.feature-value-item');
        var defaultValue = item.find('.default-value').text();
        var featureId = item.data('feature-id');
        var inputType = item.find('[name^="feature_"]').attr('type');

        if (inputType === 'radio') {
            // Установка радио-кнопок
            item.find('[name="feature_' + featureId + '"]').prop('checked', false);
            if (defaultValue) {
                var radioValue = defaultValue.toLowerCase() === 'true' ? 'true' : 'false';
                item.find('[name="feature_' + featureId + '"][value="' + radioValue + '"]')
                    .prop('checked', true);
            }
        } else if (item.find('select[name="feature_' + featureId + '"]').length) {
            // Установка выпадающего списка
            item.find('select[name="feature_' + featureId + '"]').val(defaultValue || '');
        } else if (item.find('textarea[name="feature_' + featureId + '"]').length) {
            // Установка текстового поля
            item.find('textarea[name="feature_' + featureId + '"]').val(defaultValue || '');
        } else {
            // Установка input поля
            item.find('input[name="feature_' + featureId + '"]').val(defaultValue || '');
        }

        // Подсвечиваем изменение
        item.css('border-left', '4px solid #28a745');
        setTimeout(function() {
            item.css('border-left', '1px solid #ddd');
        }, 1000);
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
        statusDiv.html(
            '<span style="padding: 5px 10px; background: ' + colors[type] +
            '; color: white; border-radius: 3px; display: inline-block;">' +
            message + '</span>'
        ).show();

        setTimeout(function() {
            statusDiv.fadeOut();
        }, 3000);
    }

    // Функция для обновления статистики
    function updateStats(stats) {
        // Здесь можно обновить отображение статистики
        // Например, если на странице есть элементы статистики
        if (stats.total !== undefined) {
            $('.completion-stats-total').text(stats.total);
        }
        if (stats.filled !== undefined) {
            $('.completion-stats-filled').text(stats.filled + '/' + stats.total);
        }
        if (stats.percentage !== undefined) {
            $('.completion-percentage').text(stats.percentage + '%');
            $('.progress-bar').css('width', stats.percentage + '%');
        }
    }

    // Функция для поиска объектов
    function initObjectSearch() {
        var objectSearch = $('.object-search');
        var contentTypeSelect = $('#id_content_type');

        if (!objectSearch.length || !contentTypeSelect.length) {
            return;
        }

        objectSearch.on('input', function() {
            var searchText = $(this).val();
            var contentTypeId = contentTypeSelect.val();

            if (searchText.length < 2 || !contentTypeId) {
                return;
            }

            $.ajax({
                url: '/admin/search/objects/',
                data: {
                    'content_type_id': contentTypeId,
                    'search': searchText
                },
                success: function(data) {
                    if (data.success && data.objects.length > 0) {
                        showObjectSuggestions(data.objects, objectSearch);
                    }
                }
            });
        });

        // При изменении типа контента очищаем поле поиска
        contentTypeSelect.on('change', function() {
            objectSearch.val('');
            $('#id_object_id').val('');
        });
    }

    // Функция для отображения подсказок по объектам
    function showObjectSuggestions(objects, searchInput) {
        // Удаляем старые подсказки
        $('#object-suggestions').remove();

        var suggestionsDiv = $('<div>', {
            id: 'object-suggestions',
            style: 'position: absolute; z-index: 1000; background: white; ' +
                   'border: 1px solid #ccc; max-height: 200px; overflow-y: auto; ' +
                   'width: ' + searchInput.outerWidth() + 'px;'
        });

        objects.forEach(function(obj) {
            var suggestion = $('<div>', {
                style: 'padding: 8px; cursor: pointer; border-bottom: 1px solid #eee;',
                text: obj.text,
                'data-id': obj.id
            });

            suggestion.on('click', function() {
                searchInput.val(obj.text);
                $('#id_object_id').val(obj.id);
                suggestionsDiv.remove();
            });

            suggestion.on('mouseenter', function() {
                $(this).css('background', '#f0f0f0');
            });

            suggestion.on('mouseleave', function() {
                $(this).css('background', 'white');
            });

            suggestionsDiv.append(suggestion);
        });

        suggestionsDiv.insertAfter(searchInput);

        // Закрываем подсказки при клике вне
        $(document).on('click', function(e) {
            if (!$(e.target).closest('#object-suggestions, .object-search').length) {
                suggestionsDiv.remove();
            }
        });
    }

    // Функция для валидации обязательных полей
    function validateRequiredFields() {
        var isValid = true;
        var firstInvalid = null;

        $('.feature-value-item').each(function() {
            var isRequired = $(this).find('.feature-value-item').css('border-left-color') === 'rgb(220, 53, 69)';
            if (isRequired) {
                var featureId = $(this).data('feature-id');
                var hasValue = false;

                // Проверяем, есть ли значение
                var inputType = $(this).find('[name^="feature_"]').attr('type');
                if (inputType === 'radio') {
                    hasValue = $(this).find('[name="feature_' + featureId + '"]:checked').length > 0;
                } else if ($(this).find('select[name="feature_' + featureId + '"]').length) {
                    hasValue = !!$(this).find('select[name="feature_' + featureId + '"]').val();
                } else if ($(this).find('textarea[name="feature_' + featureId + '"]').length) {
                    hasValue = !!$(this).find('textarea[name="feature_' + featureId + '"]').val().trim();
                } else {
                    hasValue = !!$(this).find('input[name="feature_' + featureId + '"]').val();
                }

                if (!hasValue && !firstInvalid) {
                    firstInvalid = $(this);
                    isValid = false;

                    // Подсвечиваем обязательное поле
                    $(this).css({
                        'border-left': '4px solid #dc3545',
                        'background': '#fff3cd'
                    });

                    setTimeout(function() {
                        $(this).css({
                            'border-left': '1px solid #ddd',
                            'background': '#f9f9f9'
                        });
                    }.bind(this), 2000);
                }
            }
        });

        if (!isValid && firstInvalid) {
            $('html, body').animate({
                scrollTop: firstInvalid.offset().top - 100
            }, 500);

            showStatus('Заполните все обязательные поля', 'danger');
        }

        return isValid;
    }

    // Инициализация при загрузке страницы
    $(document).ready(function() {
        // Инициализируем кнопки
        $('#save-feature-values-btn').on('click', function() {
            if (validateRequiredFields()) {
                saveFeatureValues();
            }
        });

        $('#reset-to-defaults-btn').on('click', resetToDefaults);

        // Инициализируем кнопки "Использовать значение по умолчанию"
        $(document).on('click', '.use-default-btn', function() {
            useDefaultValue(this);
        });

        // Инициализируем поиск объектов
        initObjectSearch();

        // Подсветка измененных значений
        $('.feature-value-item').each(function() {
            var defaultValue = $(this).find('.default-value').text();
            var currentValue = '';
            var featureId = $(this).data('feature-id');

            // Получаем текущее значение
            var inputType = $(this).find('[name^="feature_"]').attr('type');
            if (inputType === 'radio') {
                var checked = $(this).find('[name="feature_' + featureId + '"]:checked');
                currentValue = checked.length ? checked.val() : '';
            } else if ($(this).find('select[name="feature_' + featureId + '"]').length) {
                currentValue = $(this).find('select[name="feature_' + featureId + '"]').val() || '';
            } else if ($(this).find('textarea[name="feature_' + featureId + '"]').length) {
                currentValue = $(this).find('textarea[name="feature_' + featureId + '"]').val() || '';
            } else {
                currentValue = $(this).find('input[name="feature_' + featureId + '"]').val() || '';
            }

            // Если значение отличается от значения по умолчанию, подсвечиваем
            if (currentValue !== defaultValue) {
                $(this).css('border-left', '4px solid #007bff');
            }
        });

        // Отслеживаем изменения значений
        $(document).on('change', '[name^="feature_"]', function() {
            var item = $(this).closest('.feature-value-item');
            item.css('border-left', '4px solid #007bff');
        });

        // Подсветка обязательных полей
        $('label[for="id_name"]').append('<span style="color: red; margin-left: 3px;">*</span>');
        $('label[for="id_code"]').append('<span style="color: red; margin-left: 3px;">*</span>');
        $('label[for="id_feature_template"]').append('<span style="color: red; margin-left: 3px;">*</span>');
        $('label[for="id_content_type"]').append('<span style="color: red; margin-left: 3px;">*</span>');
        $('label[for="id_object_id"]').append('<span style="color: red; margin-left: 3px;">*</span>');
    });

})(django.jQuery);