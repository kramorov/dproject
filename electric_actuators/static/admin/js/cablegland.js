function showFullDescription(id) {
    // Открытие окна с полным описанием
    const url = '/admin/electric_actuators/actualactuator/show_description/' + id + '/';
    // const url = '/admin/show_description/' + id + '/';
    console.log('Функция showFullDescription вызвана с параметром:', id); // This will log when  the  function is triggered
    // Создаем AJAX запрос, чтобы получить описание
    fetch(url)
        .then(response => {
            if (!response.ok) {
                console.log('Network response was not ok');
                throw new Error('Network response was not ok');
            }
            return response.json(); // Expecting JSON response
        })
        .then(data => {
            console.log('Full Description:', data.full_description);
            let descriptionHtml = '<h2>Полное описание</h2>';
            data.full_description.forEach(item => {
                descriptionHtml += `<p><strong>${item.param_text}:</strong> ${item.param_value}</p>`;
            });

            // Создаем окно с информацией
            const modal = document.createElement('div');
            modal.classList.add('modal');
            modal.innerHTML = `
                <div class="modal-content">
                    <span class="close-btn" onclick="closeModal()">&times;</span>
                    ${descriptionHtml}
                </div>
            `;
            document.body.appendChild(modal);
        })
       .catch(error => {
           console.error('Ошибка операции получения данных:', error);
       });
}

function closeModal() {
    document.querySelector('.modal').remove();
}
