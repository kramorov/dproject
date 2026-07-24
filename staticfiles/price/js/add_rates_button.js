// static/price/js/add_rates_button.js
(function() {
    function addButton() {
        var tools = document.querySelector('.object-tools');
        if (!tools) {
            setTimeout(addButton, 100);
            return;
        }

        // Проверяем, не добавлена ли уже кнопка
        if (tools.querySelector('a[href="add-rates/"]')) {
            return;
        }

        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = 'add-rates/';
        a.className = 'addlink';
        a.style.cssText = 'background: #28a745; color: white; padding: 8px 15px; border-radius: 4px; text-decoration: none; display: flex; align-items: center; gap: 5px;';
        a.innerHTML = '<span style="font-size: 16px;">➕</span> Добавить курсы на дату';

        li.appendChild(a);
        tools.appendChild(li);
    }

    window.addEventListener('load', addButton);
})();