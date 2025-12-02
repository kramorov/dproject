document.addEventListener('DOMContentLoaded', function () {
    console.log("=== PNEUMATIC ACTUATOR SELECTED JS LOADED В4===");

    // Функция для обновления опций при выборе модели
    const modelSelector = document.querySelector('.pneumatic-model-selector');
    const optionSelectors = document.querySelectorAll('.pneumatic-option-selector');

    if (modelSelector) {
        modelSelector.addEventListener('change', function () {
            const modelId = this.value;
            updateOptions(modelId);
        });

        // Инициализация при загрузке
        if (modelSelector.value) {
            updateOptions(modelSelector.value);
        }
    }

    // Инициализация генератора описаний
    initDescriptionGenerator();

    function updateOptions(modelId) {
        if (!modelId) {
            // Сброс опций если модель не выбрана
            optionSelectors.forEach(select => {
                select.innerHTML = '<option value="">---------</option>';
            });
            return;
        }

        // URL для получения опций
        const url = `/admin/pneumatic_actuators/get_options/?model_id=${modelId}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                optionSelectors.forEach(select => {
                    const optionType = select.dataset.optionType;
                    const options = data[optionType] || [];

                    // Сохраняем текущее значение
                    const currentValue = select.value;

                    // Обновляем options
                    select.innerHTML = '<option value="">---------</option>';
                    options.forEach(option => {
                        const newOption = new Option(option.name, option.id, false, option.id == currentValue);
                        select.add(newOption);
                    });
                });
            })
            .catch(error => {
                console.error('Error loading options:', error);
            });
    }

    function initDescriptionGenerator() {
        const generateBtn = document.querySelector('.generate-description-btn');
        if (!generateBtn) {
            console.log('Кнопка генерации не найдена');
            return;
        }

        console.log('Кнопка генерации найдена, добавляем обработчик');
        generateBtn.addEventListener('click', function () {
            const objectId = this.dataset.objectId;
            const csrfToken = getCsrfToken();

            console.log('Клик по кнопке генерации, objectId:', objectId);

            if (!objectId) {
                alert('Ошибка: ID объекта не найден');
                return;
            }

            // Показываем индикатор загрузки
            const statusDiv = document.querySelector('.description-status');
            if (statusDiv) {
                statusDiv.innerHTML = '<span class="loading">⏳ Генерация описания...</span>';
            }
            generateBtn.disabled = true;
            const originalText = generateBtn.innerHTML;
            generateBtn.innerHTML = '⏳ Генерация...';

            // Отправляем запрос на генерацию
            console.log('Отправка запроса на генерацию...');
            fetch(`/admin/pneumatic_actuators/pneumaticactuatorselected/${objectId}/generate-description/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            })
                .then(response => {
                    console.log('Ответ получен, статус:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Данные получены:', data);
                    if (data.success) {
                        console.log('Генерация успешна, открываем новое окно');
                        // ОТКРЫВАЕМ ОПИСАНИЕ В НОВОМ ОКНЕ
                        openDescriptionInNewWindow(data.description);

                        // Обновляем поле описания (если оно видимо)
                        const descriptionField = document.querySelector('#id_description');
                        if (descriptionField) {
                            descriptionField.value = data.description;
                        }

                        if (statusDiv) {
                            statusDiv.innerHTML = '<span class="success">✅ Описание успешно сгенерировано!</span>';
                        }
                    } else {
                        console.error('Ошибка в данных:', data.message);
                        if (statusDiv) {
                            statusDiv.innerHTML = `<span class="error">❌ Ошибка: ${data.message}</span>`;
                        }
                    }
                })
                .catch(error => {
                    console.error('Fetch error:', error);
                    if (statusDiv) {
                        statusDiv.innerHTML = '<span class="error">❌ Ошибка при генерации описания</span>';
                    }
                })
                .finally(() => {
                    console.log('Завершение генерации');
                    generateBtn.disabled = false;
                    generateBtn.innerHTML = originalText;
                });
        });
    }

    // Функция для открытия описания в новом окне
    function openDescriptionInNewWindow(descriptionText) {
    console.log('Открытие нового окна с описанием');

    // Очищаем текст перед обработкой
    const cleanedText = descriptionText
        .replace(/\n{3,}/g, '\n\n')  // Заменяем 3+ переноса на 2
        .replace(/\n{2}/g, '\n');    // Заменяем 2 переноса на 1

    // Функция для экранирования HTML (но НЕ для таблиц)
    function escapeHtml(text) {
        // Разделяем текст на части: HTML таблицы и обычный текст
        const parts = text.split(/(<table[\s\S]*?<\/table>)/);

        return parts.map(part => {
            if (part.startsWith('<table') && part.endsWith('</table>')) {
                // Это HTML таблица - не экранируем
                return part;
            } else {
                // Это обычный текст - экранируем и заменяем переносы строк
                const div = document.createElement('div');
                div.textContent = part;
                return div.innerHTML.replace(/\n/g, '<br>');
            }
        }).join('');
    }

        // Размеры окна
        const width = 1000;
        const height = 700;
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;

        // Параметры окна
        const features = `
            width=${width},
            height=${height},
            left=${left},
            top=${top},
            resizable=yes,
            scrollbars=yes,
            toolbar=no,
            menubar=no,
            location=no,
            status=no
        `.replace(/\s+/g, '');

        // Открываем новое окно
        const newWindow = window.open('', 'Описание пневмопривода', features);

        if (!newWindow) {
            alert('Пожалуйста, разрешите всплывающие окна для этого сайта');
            return;
        }

        // Формируем HTML для нового окна
        newWindow.document.write(`
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Описание пневмопривода</title>
                <style>
                /* Добавьте стили для таблицы */
                .description-content table {
                    border-collapse: collapse;
                    margin: 20px 0;
                    width: 100%;
                    font-size: 13px;
                    font-family: inherit;
                }
                
                .description-content th,
                .description-content td {
                    border: 1px solid #ddd;
                    padding: 8px 12px;
                    text-align: center;
                    min-width: 80px;
                }
                
                .description-content th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
                
                .description-content tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background: #f5f5f5;
                        padding: 20px;
                        overflow-y: auto;
                        min-height: 100vh;
                    }
                    
                    .container {
                        max-width: none;
                        width: 95%;
                        margin: 0 auto;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        padding: 30px;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                    }
                    
                    h1 {
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                        font-size: 24px;
                    }
                    
                    .description-content {
                        white-space: pre-wrap;
                        font-size: 14px;
                        line-height: 1.8;
                        max-height: none;
                        overflow: visible;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    }
                    
                    .description-content p {
                        margin-bottom: 10px;
                    }
                    
                    .description-content table {
                        border-collapse: collapse;
                        margin: 20px 0;
                        width: 100%;
                        font-size: 13px;
                        font-family: inherit;
                    }
                    
                    .description-content th,
                    .description-content td {
                        border: 1px solid #ddd;
                        padding: 8px 12px;
                        text-align: center;
                    }
                    
                    .description-content th {
                        background-color: #f8f9fa;
                        font-weight: bold;
                    }
                    
                    .description-content tr:nth-child(even) {
                        background-color: #f9f9f9;
                    }
                    
                    .controls {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        z-index: 1000;
                        background: white;
                        padding: 10px;
                        border-radius: 6px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                        display: flex;
                        gap: 10px;
                    }
                    
                    .btn {
                        padding: 8px 15px;
                        background: #3498db;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: background 0.3s;
                        white-space: nowrap;
                    }
                    
                    .btn:hover {
                        background: #2980b9;
                    }
                    
                    .btn-copy {
                        background: #2ecc71;
                    }
                    
                    .btn-copy:hover {
                        background: #27ae60;
                    }
                    
                    .btn-print {
                        background: #9b59b6;
                    }
                    
                    .btn-print:hover {
                        background: #8e44ad;
                    }
                    
                    .btn-close {
                        background: #e74c3c;
                    }
                    
                    .btn-close:hover {
                        background: #c0392b;
                    }
                    
                    @media print {
                        .controls {
                            display: none;
                        }
                        
                        body {
                            background: white;
                            padding: 0;
                        }
                        
                        .container {
                            box-shadow: none;
                            padding: 0;
                        }
                    }
                    
                    /* Для длинных таблиц */
                    .description-content pre {
                        overflow-x: auto;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                </style>
            </head>
            <body>
                <div class="controls">
                    <button class="btn btn-copy" id="copy-btn">📋 Копировать</button>
                    <button class="btn btn-print" id="print-btn">🖨️ Печать</button>
                    <button class="btn btn-close" id="close-btn">✖️ Закрыть</button>
                </div>
                
                <div class="container">
                    <h1>Описание пневмопривода</h1>
                    <div class="description-content" id="description-content">
                         ${escapeHtml(cleanedText)}
                    </div>
                </div>
                
                <script>
                    // Функция для копирования в буфер обмена
                    document.getElementById('copy-btn').addEventListener('click', function() {
                        const content = document.getElementById('description-content');
                        const text = content.innerText || content.textContent;
                        
                        navigator.clipboard.writeText(text).then(function() {
                            const btn = this;
                            const originalText = btn.innerHTML;
                            btn.innerHTML = '✅ Скопировано!';
                            btn.style.background = '#27ae60';
                            
                            setTimeout(function() {
                                btn.innerHTML = originalText;
                                btn.style.background = '#2ecc71';
                            }, 2000);
                        }.bind(this)).catch(function(err) {
                            alert('Ошибка при копировании: ' + err);
                        });
                    });
                    
                    // Функция для печати
                    document.getElementById('print-btn').addEventListener('click', function() {
                        window.print();
                    });
                    
                    // Функция для закрытия окна
                    document.getElementById('close-btn').addEventListener('click', function() {
                        window.close();
                    });
                    
                    // Автоматически прокручиваем в начало
                    window.scrollTo(0, 0);
                    
                    // Фокус на контент
                    document.getElementById('description-content').focus();
                </script>
            </body>
            </html>
        `);

        newWindow.document.close();
        newWindow.focus();
        console.log('Новое окно открыто успешно');
    }

    function getCsrfToken() {
        // Получаем CSRF токен из cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Автоматическая генерация при изменении опций (опционально)
    const autoGenerateCheckbox = document.getElementById('id_auto_generate');
    if (autoGenerateCheckbox && autoGenerateCheckbox.checked) {
        const optionFields = document.querySelectorAll('select[name^="selected_"]');
        optionFields.forEach(field => {
            field.addEventListener('change', function () {
                setTimeout(checkAndGenerate, 1000);
            });
        });
    }

    function checkAndGenerate() {
        // Проверяем, все ли обязательные поля заполнены
        // и генерируем описание автоматически
        const generateBtn = document.querySelector('.generate-description-btn');
        if (generateBtn) {
            generateBtn.click();
        }
    }
});