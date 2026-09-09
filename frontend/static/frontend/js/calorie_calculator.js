document.getElementById('calorie-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const errorEl = document.getElementById('calorie-error');
    const resultEl = document.getElementById('calorie-result');
    errorEl.textContent = '';
    resultEl.textContent = '';

    const payload = {
        target_weight_change: document.getElementById('target-weight-change').value,
        days: document.getElementById('calorie-days').value,
    };

    const gender = document.getElementById('calorie-gender').value;
    const age = document.getElementById('calorie-age').value;
    const height = document.getElementById('calorie-height').value;
    const weight = document.getElementById('calorie-weight').value;
    const activity = document.getElementById('calorie-activity').value;

    if (gender) payload.gender = gender;
    if (age) payload.age = age;
    if (height) payload.height = height;
    if (weight) payload.weight = weight;
    if (activity) payload.activity_level = activity;

    const response = await apiFetch('/analytics/calculator/', {
        method: 'POST',
        body: JSON.stringify(payload),
    });

    if (!response) return;

    if (!response.ok) {
        const errorData = await response.json();
        errorEl.textContent = errorData.detail || 'Не удалось рассчитать. Проверьте профиль (пол, рост, дата рождения) и наличие записей веса.';
        return;
    }

    const data = await response.json();
    resultEl.textContent =
        `Базовый метаболизм (BMR): ${data.bmr} ккал | ` +
        `Норма для поддержания веса: ${data.maintenance_calories} ккал | ` +
        `Рекомендуемая калорийность: ${data.target_calories} ккал/день`;
});