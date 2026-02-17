// electric_actuators/static/admin/js/description_handler.js
(function($) {
    'use strict';

    $(document).ready(function() {
        // Кнопка "Показать описание"
        $('#show-description-btn').click(function() {
            var instanceId = getInstanceId();

            $.ajax({
                url: `/api/description/${instanceId}/html/`,
                type: 'GET',
                success: function(response) {
                    if (response.success) {
                        showModal(response.html, instanceId);
                    }
                }
            });
        });

        function showModal(html, instanceId) {
            var $modal = $(
                '<div class="description-modal" style="' +
                'position: fixed; top: 0; left: 0; width: 100%; height: 100%; ' +
                'background: rgba(0,0,0,0.5); z-index: 10000; display: flex; ' +
                'align-items: center; justify-content: center;">' +
                '<div class="modal-content" style="' +
                'background: white; padding: 20px; border-radius: 8px; ' +
                'max-width: 800px; max-height: 80vh; overflow-y: auto; ' +
                'width: 90%;">' +
                '<div class="modal-header" style="display: flex; justify-content: space-between; margin-bottom: 15px;">' +
                '<h2 style="margin: 0;">Детальное описание</h2>' +
                '<div>' +
                '<a href="/api/description/' + instanceId + '/docx/" class="button" style="margin-right: 10px;">Скачать Word</a>' +
                '<button class="close-modal button" style="background: #dc3545;">×</button>' +
                '</div>' +
                '</div>' +
                '<div class="modal-body">' + html + '</div>' +
                '</div>' +
                '</div>'
            );

            $('body').append($modal);

            $modal.find('.close-modal').click(function() {
                $modal.remove();
            });
        }

        function getInstanceId() {
            var path = window.location.pathname;
            var matches = path.match(/\/(\d+)\//);
            return matches ? matches[1] : null;
        }
    });
})(django.jQuery);