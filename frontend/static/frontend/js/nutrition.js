let itemCounter = 0;

function createItemRow() {
    itemCounter += 1;
    const id = itemCounter;

    const row = document.createElement('div');
    row.className = 'item-row';
    row.dataset.itemId = id;
    row.innerHTML = `
        <input type="text" class="item-name" placeholder="Название продукта" required>
        <label><input type="checkbox" class="item-is-liquid"> Жидкость</label>
        <input type="number" class="item-amount" placeholder="Масса" required>
        <input type="number" step="0.01" class="item-calories" placeholder="Ккал" required>
        <input type="number" step="0.01" class="item-protein" placeholder="Белки" required>
        <input type="number" step="0.01" class="item-fat" placeholder="Жиры" required>
        <input type="number" step="0.01" class="item-carbs" placeholder="Углеводы" required>
        <button type="button" class="remove-item-btn">Удалить</button>
    `;

    row.querySelector('.remove-item-btn').addEventListener('click', () => row.remove());

    return row;
}

document.getElementById('add-item-btn').addEventListener('click', () => {
    document.getElementById('items-container').appendChild(createItemRow());
});

function collectItems() {
    const rows = document.querySelectorAll('#items-container .item-row');
    return Array.from(rows).map(row => ({
        name: row.querySelector('.item-name').value,
        is_liquid: row.querySelector('.item-is-liquid').checked,
        amount: row.querySelector('.item-amount').value,
        calories: row.querySelector('.item-calories').value,
        protein: row.querySelector('.item-protein').value,
        fat: row.querySelector('.item-fat').value,
        carbs: row.querySelector('.item-carbs').value,
    }));
}

function renderDailySummary(meals) {
    const today = new Date().toISOString().slice(0, 10);
    const todayMeals = meals.filter(m => m.date === today);

    const totals = { calories: 0, protein: 0, fat: 0, carbs: 0 };
    todayMeals.forEach(meal => {
        meal.items.forEach(item => {
            totals.calories += parseFloat(item.calories);
            totals.protein += parseFloat(item.protein);
            totals.fat += parseFloat(item.fat);
            totals.carbs += parseFloat(item.carbs);
        });
    });

    document.getElementById('daily-summary').textContent =
        `Калории: ${totals.calories.toFixed(0)} ккал | ` +
        `Белки: ${totals.protein.toFixed(1)} г | ` +
        `Жиры: ${totals.fat.toFixed(1)} г | ` +
        `Углеводы: ${totals.carbs.toFixed(1)} г`;
}

async function loadMeals() {
    const response = await apiFetch('/nutrition/meals/');
    if (!response || !response.ok) return;

    const meals = await response.json();
    renderDailySummary(meals);
    const listEl = document.getElementById('meals-list');
    listEl.innerHTML = '';

    const mealTypeLabels = {
        breakfast: 'Завтрак',
        lunch: 'Обед',
        dinner: 'Ужин',
        snack: 'Перекус',
    };

    meals
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .forEach(meal => {
            const block = document.createElement('div');
            block.className = 'card';

            const itemsHtml = meal.items.map(item => `
                <li>${item.name} — ${item.amount} г/мл
                    (${item.calories} ккал)</li>
            `).join('');

            block.innerHTML = `
                <strong>${meal.date} — ${mealTypeLabels[meal.meal_type] || meal.meal_type}</strong>
                <ul>${itemsHtml}</ul>
            `;

            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Удалить приём пищи';
            deleteBtn.addEventListener('click', async () => {
                const resp = await apiFetch(`/nutrition/meals/${meal.id}/`, { method: 'DELETE' });
                if (resp && resp.ok) {
                    await loadMeals();
                }
            });
            block.appendChild(deleteBtn);

            listEl.appendChild(block);
        });
}

document.getElementById('meal-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const errorEl = document.getElementById('meal-error');
    errorEl.textContent = '';

    const items = collectItems();
    if (items.length === 0) {
        errorEl.textContent = 'Добавьте хотя бы один продукт';
        return;
    }

    const payload = {
        meal_type: document.getElementById('meal-type').value,
        date: document.getElementById('meal-date').value,
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

    document.getElementById('meal-form').reset();
    document.getElementById('items-container').innerHTML = '';
    await loadMeals();
});

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('items-container').appendChild(createItemRow());
    loadMeals();
});
