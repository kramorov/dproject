// features/static/features/js/admin-equipment-type.js
(function($) {
    'use strict';

    $(document).ready(function() {
        // Функция для обновления уровня при выборе родителя
        function updateLevelOnParentChange() {
            var parentSelect = $('#id_parent');
            var levelInput = $('#id_level');

            parentSelect.on('change', function() {
                var parentId = $(this).val();
                if (parentId) {
                    // AJAX запрос для получения уровня родителя
                    $.ajax({
                        url: '/admin/features/equipmenttype/get_level/',
                        data: {
                            'parent_id': parentId
                        },
                        success: function(data) {
                            if (data.success) {
                                levelInput.val(data.level + 1);
                            }
                        }
                    });
                } else {
                    levelInput.val(0);
                }
            });
        }

        // Функция для поиска типов оборудования
        function initSearch() {
            var searchInput = $('<input>', {
                type: 'text',
                id: 'equipment-type-search',
                placeholder: 'Поиск типов оборудования...',
                style: 'margin-bottom: 10px; padding: 5px; width: 100%;'
            });

            // Вставляем поле поиска перед таблицей
            $('.field-hierarchy_visualization').before(searchInput);

            searchInput.on('keyup', function() {
                var searchText = $(this).val().toLowerCase();
                $('#hierarchy-visualization ul li').each(function() {
                    var text = $(this).text().toLowerCase();
                    if (text.indexOf(searchText) > -1) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            });
        }

        // Функция для отображения дерева
        function initTreeView() {
            var treeBtn = $('<button>', {
                type: 'button',
                class: 'button',
                text: '🌳 Показать полное дерево',
                style: 'margin: 10px 0;'
            });

            treeBtn.on('click', function() {
                $.ajax({
                    url: '/admin/features/equipmenttype/get_tree/',
                    success: function(data) {
                        if (data.success) {
                            showTreeModal(data.tree);
                        }
                    }
                });
            });

            $('.field-hierarchy_visualization').before(treeBtn);
        }

        // Модальное окно для дерева
        function showTreeModal(treeData) {
            var modal = $('<div>', {
                id: 'equipment-type-tree-modal',
                style: 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; ' +
                       'background: rgba(0,0,0,0.5); z-index: 1000; display: flex; ' +
                       'justify-content: center; align-items: center;'
            });

            var modalContent = $('<div>', {
                style: 'background: white; padding: 20px; border-radius: 5px; ' +
                       'max-width: 80%; max-height: 80%; overflow: auto;'
            });

            var closeBtn = $('<button>', {
                type: 'button',
                class: 'button',
                text: '✕ Закрыть',
                style: 'float: right; margin-bottom: 10px;'
            });

            closeBtn.on('click', function() {
                modal.remove();
            });

            modalContent.append(closeBtn);
            modalContent.append($('<h3>').text('Полное дерево типов оборудования'));
            modalContent.append($('<div>').html(treeData));

            modal.append(modalContent);
            $('body').append(modal);
        }

        // Инициализация всех функций
        updateLevelOnParentChange();
        initSearch();
        initTreeView();

        // Подсветка обязательных полей
        $('label[for="id_name"]').append('<span style="color: red; margin-left: 3px;">*</span>');
        $('label[for="id_code"]').append('<span style="color: red; margin-left: 3px;">*</span>');
    });

})(django.jQuery);