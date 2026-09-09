function createEditableItemRow(item) {
    const row = document.createElement('div');
    row.className = 'item-row';
    row.innerHTML = `
        <input type="text" class="item-name" value="${item.name}" required>
        <label><input type="checkbox" class="item-is-liquid" ${item.is_liquid ? 'checked' : ''}> Жидкость</label>
        <input type="number" class="item-amount" value="${item.amount}" required>
        <input type="number" step="0.01" class="item-calories" value="${item.calories}" required>
        <input type="number" step="0.01" class="item-protein" value="${item.protein}" required>
        <input type="number" step="0.01" class="item-fat" value="${item.fat}" required>
        <input type="number" step="0.01" class="item-carbs" value="${item.carbs}" required>
        <button type="button" class="remove-item-btn">Удалить</button>
    `;
    row.querySelector('.remove-item-btn').addEventListener('click', () => row.remove());
    return row;
}

document.getElementById('ai-parse-btn').addEventListener('click', async () => {
    const description = document.getElementById('ai-description').value.trim();
    const errorEl = document.getElementById('ai-error');
    errorEl.textContent = '';

    if (!description) {
        errorEl.textContent = 'Введите описание еды';
        return;
    }

    const response = await apiFetch('/nutrition/ai-parse/', {
        method: 'POST',
        body: JSON.stringify({ description }),
    });

    if (!response) return;

    if (!response.ok) {
        const errorData = await response.json();
        errorEl.textContent = errorData.detail || 'Не удалось распознать описание';
        return;
    }

    const data = await response.json();
    const container = document.getElementById('ai-items-container');
    container.innerHTML = '';
    data.items.forEach(item => container.appendChild(createEditableItemRow(item)));

    document.getElementById('ai-preview-container').style.display = 'block';
});

document.getElementById('ai-cancel-btn').addEventListener('click', () => {
    document.getElementById('ai-preview-container').style.display = 'none';
    document.getElementById('ai-items-container').innerHTML = '';
    document.getElementById('ai-description').value = '';
});

document.getElementById('ai-confirm-btn').addEventListener('click', async () => {
    const errorEl = document.getElementById('ai-error');
    errorEl.textContent = '';

    const rows = document.querySelectorAll('#ai-items-container .item-row');
    const items = Array.from(rows).map(row => ({
        name: row.querySelector('.item-name').value,
        is_liquid: row.querySelector('.item-is-liquid').checked,
        amount: row.querySelector('.item-amount').value,
        calories: row.querySelector('.item-calories').value,
        protein: row.querySelector('.item-protein').value,
        fat: row.querySelector('.item-fat').value,
        carbs: row.querySelector('.item-carbs').value,
    }));

    if (items.length === 0) {
        errorEl.textContent = 'Нет продуктов для сохранения';
        return;
    }

    const payload = {
        meal_type: document.getElementById('ai-meal-type').value,
        date: document.getElementById('ai-meal-date').value,
        items: items,
    };

    const response = await apiFetch('/nutrition/meals/', {
        method: 'POST',
        body: JSON.stringify(payload),
    });

    if (!response || !response.ok) {
        errorEl.textContent = 'Ошибка сохранения приёма пищи';
        return;
    }

    document.getElementById('ai-preview-container').style.display = 'none';
    document.getElementById('ai-items-container').innerHTML = '';
    document.getElementById('ai-description').value = '';
    await loadMeals();
});