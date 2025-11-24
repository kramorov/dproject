// Убедитесь, что jQuery доступен
if (typeof django !== 'undefined' && django.jQuery) {
    (function($) {
        'use strict';

        $(document).ready(function() {
            // Функция для обновления фильтра
            function updateDnFilter() {
                var minVal = $('#id_min_diameter_filter').val();
                var maxVal = $('#id_max_diameter_filter').val();

                // Сохраняем текущие параметры URL
                var urlParams = new URLSearchParams(window.location.search);

                // Обновляем параметры фильтра
                if (minVal) {
                    urlParams.set('min_diameter_filter', minVal);
                } else {
                    urlParams.delete('min_diameter_filter');
                }

                if (maxVal) {
                    urlParams.set('max_diameter_filter', maxVal);
                } else {
                    urlParams.delete('max_diameter_filter');
                }

                // Перезагружаем страницу с новыми параметрами
                window.location.search = urlParams.toString();
            }

            // Ждем полной загрузки DOM
            $(function() {
                // Обработчики событий для полей фильтра
                $('#id_min_diameter_filter, #id_max_diameter_filter').on('change', function() {
                    setTimeout(updateDnFilter, 800);
                });

                // Обработчик для клавиши Enter
                $('#id_min_diameter_filter, #id_max_diameter_filter').on('keypress', function(e) {
                    if (e.which === 13) {
                        updateDnFilter();
                    }
                });

                // Показываем текущий активный фильтр
                var urlParams = new URLSearchParams(window.location.search);
                var currentMin = urlParams.get('min_diameter_filter');
                var currentMax = urlParams.get('max_diameter_filter');

                if (currentMin || currentMax) {
                    var filterText = 'Текущий фильтр DN: ';
                    if (currentMin) filterText += 'от ' + currentMin;
                    if (currentMin && currentMax) filterText += ' ';
                    if (currentMax) filterText += 'до ' + currentMax;

                    // Добавляем информацию о фильтре
                    $('.field-dn').before(
                        '<div class="form-row" style="background: #f8f8f8; padding: 8px; border-radius: 4px; margin-bottom: 10px;">' +
                        '<div style="color: #666; font-size: 12px;">' + filterText +
                        ' <a href="?" style="margin-left: 10px; color: #417690;">[сбросить]</a></div>' +
                        '</div>'
                    );
                }
            });
        });

    })(django.jQuery);
} else {
    console.error('django.jQuery is not available');
}