import pytest
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal

from users.models import User
from weight.models import WeightEntry
from analytics.services.weight_forecast import forecast_weight
from analytics.services.weight_forecast_queries import FORECAST_WINDOW_DAYS

pytestmark = pytest.mark.django_db

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpass123')

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def user_with_weight_history():
    new_user = User.objects.create_user(username='testuser2', password='testpass123')
    today = date.today()
    weights = [Decimal('40'), Decimal('40.5'), Decimal('41'), Decimal('41.5'), Decimal('42')]
    for i, weight in enumerate(weights):
        WeightEntry.objects.create(
            user=new_user,
            date=today - timedelta(days=len(weights) - 1 - i),
            weight=weight,
        )
    return new_user

@pytest.fixture
def api_client_with_weight_history(user_with_weight_history):
    client = APIClient()
    client.force_authenticate(user=user_with_weight_history)
    return client

def test_forecast_returns_200_with_sufficient_entries(api_client_with_weight_history):
    """
    Проверяем, что при наличии достаточного количества записей веса за окно
    (минимум 2) запрос прогноза возвращает 200 и структуру ответа с ключами
    historical_fit, forecast, r_squared, confidence_level, data_points_used.
    """
    response = api_client_with_weight_history.post('/api/analytics/forecast/', {
        'days_ahead': '5'
    })

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data.keys()) == {
        'historical_fit', 'forecast', 'r_squared', 'confidence_level', 'data_points_used'
    }
    assert response.data['data_points_used'] == 5
    assert len(response.data['historical_fit']) == 5
    assert len(response.data['forecast']) == 5
    assert response.data['confidence_level'] in ('high', 'medium', 'low')

def test_forecast_returns_400_with_insufficient_entries(api_client):
    """
    Проверяем случай, когда записей веса меньше двух (или их нет вообще)
    за окно в 14 дней. Ожидаем 400 и сообщение о недостатке данных.
    """
    response = api_client.post('/api/analytics/forecast/', {
        'days_ahead': '14'
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_forecast_ignores_entries_outside_window(api_client, user):
    """
    Проверяем, что записи веса старше FORECAST_WINDOW_DAYS не участвуют
    в прогнозе. Создаём записи и внутри, и снаружи окна (например, 20 дней назад),
    и проверяем, что data_points_used учитывает только записи внутри окна.
    """
    today = date.today()

    # Записи внутри окна (последние 14 дней)
    WeightEntry.objects.create(user=user, date=today - timedelta(days=2), weight=Decimal('70'))
    WeightEntry.objects.create(user=user, date=today - timedelta(days=1), weight=Decimal('70.5'))
    WeightEntry.objects.create(user=user, date=today, weight=Decimal('71'))

    # Записи снаружи окна (значительно раньше FORECAST_WINDOW_DAYS)
    WeightEntry.objects.create(
        user=user, date=today - timedelta(days=FORECAST_WINDOW_DAYS + 5), weight=Decimal('90')
    )
    WeightEntry.objects.create(
        user=user, date=today - timedelta(days=FORECAST_WINDOW_DAYS + 10), weight=Decimal('95')
    )

    response = api_client.post('/api/analytics/forecast/', {'days_ahead': '5'})

    assert response.status_code == status.HTTP_200_OK
    assert response.data['data_points_used'] == 3

def test_forecast_uses_default_days_ahead_when_not_provided(api_client_with_weight_history):
    """
    Проверяем, что если days_ahead не передан в запросе, используется
    значение по умолчанию (14), и массив forecast содержит соответствующее
    количество точек.
    """
    response = api_client_with_weight_history.post('/api/analytics/forecast/', {})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['forecast']) == 14

def test_forecast_respects_custom_days_ahead(api_client_with_weight_history):
    """
    Проверяем, что при явно переданном days_ahead (например, 5) массив
    forecast содержит ровно столько точек, сколько запрошено.
    """
    response = api_client_with_weight_history.post('/api/analytics/forecast/', {
        'days_ahead': '5'
    })

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['forecast']) == 5

def test_forecast_rejects_days_ahead_above_max(api_client_with_weight_history):
    """
    Проверяем, что days_ahead больше максимально допустимого значения (30)
    отклоняется с 400 (валидация сериализатора).
    """
    response = api_client_with_weight_history.post('/api/analytics/forecast/', {
        'days_ahead': '31'
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_forecast_requires_authentication():
    """
    Проверяем, что без JWT-аутентификации запрос возвращает 401.
    """
    client = APIClient()
    response = client.post('/api/analytics/forecast/', {'days_ahead': '5'})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_forecast_response_matches_service_calculation(api_client_with_weight_history, user_with_weight_history):
    """
    Сквозная проверка точности: сравниваем значения из ответа API
    с результатом прямого вызова forecast_weight на тех же данных
    (аналогично тому, как сравнивали калькулятор калорий с эталонной функцией).
    """
    response = api_client_with_weight_history.post('/api/analytics/forecast/', {
        'days_ahead': '5'
    })

    entries = list(WeightEntry.objects.filter(user=user_with_weight_history).order_by('date'))
    expected = forecast_weight(entries, 5)

    assert response.status_code == status.HTTP_200_OK
    assert Decimal(str(response.data['r_squared'])) == expected.r_squared
    assert response.data['confidence_level'] == expected.confidence_level
    assert response.data['data_points_used'] == expected.data_points_used

    for actual_point, expected_point in zip(response.data['forecast'], expected.forecast):
        assert actual_point['date'] == expected_point.date
        assert Decimal(str(actual_point['predicted_weight'])) == expected_point.predicted_weight