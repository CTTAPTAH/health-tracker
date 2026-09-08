let chartInstance = null;

async function loadWeightList() {
    const response = await apiFetch('/weight/');
    if (!response || !response.ok) return;

    const entries = await response.json();
    const listEl = document.getElementById('weight-list');
    listEl.innerHTML = '';

    entries
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 10)
        .forEach(entry => {
            const li = document.createElement('li');
            li.textContent = `${entry.date}: ${entry.weight} кг`;
            listEl.appendChild(li);
        });

    return entries;
}

async function loadForecast() {
    const response = await apiFetch('/analytics/forecast/', {
        method: 'POST',
        body: JSON.stringify({ days_ahead: 14 }),
    });
    if (!response || !response.ok) return null;
    return await response.json();
}

function renderChart(historyEntries, forecastData, showForecast) {
    const ctx = document.getElementById('weight-chart');

    const historyPoints = historyEntries
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .map(e => ({ x: e.date, y: e.weight }));

    const datasets = [
        {
            label: 'Фактический вес',
            data: historyPoints,
            borderColor: '#2b6777',
            backgroundColor: '#2b6777',
        },
    ];

    if (showForecast && forecastData) {
        datasets.push({
            label: 'Линия регрессии',
            data: forecastData.historical_fit.map(p => ({ x: p.date, y: p.predicted_weight })),
            borderColor: '#888',
            borderDash: [5, 5],
            pointRadius: 0,
        });
        datasets.push({
            label: 'Прогноз',
            data: forecastData.forecast.map(p => ({ x: p.date, y: p.predicted_weight })),
            borderColor: '#e67e22',
            borderDash: [5, 5],
            pointRadius: 2,
        });
    }

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        tooltipFormat: 'dd.MM.yyyy',
                        displayFormats: { day: 'dd.MM' },
                    },
                },
            },
        },
    });
}

async function refreshDashboard() {
    const entries = await loadWeightList();
    const forecastData = await loadForecast();
    const showForecast = document.getElementById('show-forecast-checkbox').checked;
    renderChart(entries || [], forecastData, showForecast);
}

document.getElementById('add-weight-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const weight = document.getElementById('weight-value').value;
    const date = document.getElementById('weight-date').value;
    const errorEl = document.getElementById('weight-error');
    errorEl.textContent = '';

    const response = await apiFetch('/weight/', {
        method: 'POST',
        body: JSON.stringify({ weight, date }),
    });

    if (!response || !response.ok) {
        errorEl.textContent = 'Ошибка добавления записи';
        return;
    }

    document.getElementById('add-weight-form').reset();
    await refreshDashboard();
});

document.getElementById('show-forecast-checkbox').addEventListener('change', refreshDashboard);

document.addEventListener('DOMContentLoaded', refreshDashboard);