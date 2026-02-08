// electric_actuators/static/admin/js/electric_selected_admin.js
(function($) {
    'use strict';

    $(document).ready(function() {
        console.log('Electric actuator selected admin JS loaded');

        // Флаг чтобы предотвратить множественные отправки
        var isSubmitting = false;

        // Добавление кнопок рядом с полем выбора модели
        function addButtonsNearModelField() {
            var $modelFieldContainer = $('.field-selected_model_line_item');

            if (!$modelFieldContainer.length) {
                setTimeout(addButtonsNearModelField, 500);
                return;
            }

            // Проверяем, не добавили ли уже кнопки
            if ($modelFieldContainer.find('.model-actions').length) {
                return;
            }

            console.log('Adding buttons near model field');

            // Создаем контейнер для кнопок
            var $actionsContainer = $(
                '<div class="model-actions" style="' +
                'margin-top: 10px; ' +
                'padding: 10px; ' +
                'background-color: #f8f9fa; ' +
                'border: 1px solid #dee2e6; ' +
                'border-radius: 4px;' +
                '">' +
                '<p style="font-weight: bold; margin-bottom: 8px; color: #495057; font-size: 13px;">Действия после выбора модели:</p>' +
                '<div class="action-buttons" style="display: flex; flex-wrap: wrap; gap: 8px;">' +
                '</div>' +
                '</div>'
            );

            var $buttonsContainer = $actionsContainer.find('.action-buttons');

            // Кнопка "Применить дефолтные опции"
            var $applyBtn = $('<button type="button" class="button" style="' +
                'background-color: #20c997; ' +
                'border-color: #20c997; ' +
                'color: white; ' +
                'font-weight: bold; ' +
                'padding: 6px 12px; ' +
                'font-size: 12px; ' +
                'border-radius: 4px; ' +
                'cursor: pointer; ' +
                'flex: 1; ' +
                'min-width: 180px;' +
                '">🔄 Применить опции</button>')
                .click(function(e) {
                    e.preventDefault();

                    if (isSubmitting) return;
                    isSubmitting = true;

                    var modelId = $('#id_selected_model_line_item').val();
                    if (!modelId) {
                        alert('Сначала выберите модель');
                        isSubmitting = false;
                        return;
                    }

                    if (confirm('Применить дефолтные опции из выбранной модели?\n\nЭто заполнит все опции значениями по умолчанию для этой модели.')) {
                        console.log('Applying default options for model:', modelId);

                        // СОХРАНЯЕМ текущие данные формы
                        var $form = $('form');
                        var formData = new FormData($form[0]);

                        // Добавляем флаг
                        formData.append('apply_defaults', '1');

                        // Отправляем форму с сохраненными данными
                        $.ajax({
                            url: $form.attr('action'),
                            type: 'POST',
                            data: formData,
                            processData: false,
                            contentType: false,
                            beforeSend: function(xhr) {
                                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                            },
                            success: function(response) {
                                console.log('Default options applied successfully');
                                // Перезагружаем страницу для отображения изменений
                                window.location.reload();
                            },
                            error: function(xhr, status, error) {
                                console.error('Error applying default options:', error);
                                alert('Ошибка при применении дефолтных опций: ' + error);
                                isSubmitting = false;
                            }
                        });
                    } else {
                        isSubmitting = false;
                    }
                });

            // Кнопка "Сгенерировать имя и код"
            var $generateBtn = $('<button type="button" class="button" style="' +
                'background-color: #17a2b8; ' +
                'border-color: #17a2b8; ' +
                'color: white; ' +
                'font-weight: bold; ' +
                'padding: 6px 12px; ' +
                'font-size: 12px; ' +
                'border-radius: 4px; ' +
                'cursor: pointer; ' +
                'flex: 1; ' +
                'min-width: 180px;' +
                '">📝 Сгенерировать</button>')
                .click(function(e) {
                    e.preventDefault();

                    if (isSubmitting) return;
                    isSubmitting = true;

                    var modelId = $('#id_selected_model_line_item').val();
                    if (!modelId) {
                        alert('Сначала выберите модель');
                        isSubmitting = false;
                        return;
                    }

                    if (confirm('Сгенерировать название и код на основе выбранной модели и опций?')) {
                        console.log('Generating name/code for model:', modelId);

                        var $form = $('form');
                        var formData = new FormData($form[0]);
                        formData.append('generate_name_code', '1');

                        $.ajax({
                            url: $form.attr('action'),
                            type: 'POST',
                            data: formData,
                            processData: false,
                            contentType: false,
                            beforeSend: function(xhr) {
                                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                            },
                            success: function(response) {
                                console.log('Name/code generated successfully');
                                window.location.reload();
                            },
                            error: function(xhr, status, error) {
                                console.error('Error generating name/code:', error);
                                alert('Ошибка при генерации имени и кода: ' + error);
                                isSubmitting = false;
                            }
                        });
                    } else {
                        isSubmitting = false;
                    }
                });

            // Добавляем кнопки в контейнер
            $buttonsContainer.append($applyBtn);
            $buttonsContainer.append($generateBtn);

            // Добавляем подсказку
            $actionsContainer.append(
                '<p style="margin: 8px 0 0 0; font-size: 11px; color: #6c757d;">' +
                'Кнопки станут активны после выбора модели' +
                '</p>'
            );

            // Вставляем контейнер после поля выбора модели
            $modelFieldContainer.append($actionsContainer);
            console.log('Buttons added successfully');

            // Обновляем состояние кнопок при изменении выбора модели
            $('#id_selected_model_line_item').on('change', function() {
                var modelId = $(this).val();
                var buttons = $actionsContainer.find('button');

                if (modelId) {
                    buttons.prop('disabled', false).css('opacity', '1');
                    console.log('Model selected, buttons enabled');
                } else {
                    buttons.prop('disabled', true).css('opacity', '0.6');
                    console.log('No model selected, buttons disabled');
                }
            });

            // Изначальное состояние кнопок
            var initialModelId = $('#id_selected_model_line_item').val();
            if (!initialModelId) {
                $actionsContainer.find('button').prop('disabled', true).css('opacity', '0.6');
            }
        }

        // Функция для получения CSRF токена
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        // Инициализация
        addButtonsNearModelField();

        // Повторная попытка через время
        setTimeout(addButtonsNearModelField, 1000);

        console.log('Electric actuator selected admin JS initialization complete');
    });

})(django.jQuery);