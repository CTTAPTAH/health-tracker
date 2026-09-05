import pytest
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from decimal import Decimal

from users.models import User
from weight.models import WeightEntry
from analytics.services.calorie_calculator import calculate_target_calories

@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpass123')

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def api_client_not_jwt_authentication(user):
    client = APIClient()
    return client

@pytest.fixture
def user_with_profile(user):
    user.gender = 'male'
    user.height = 180
    user.birth_date = date(2006, 1, 9)
    user.save()

    WeightEntry.objects.create(user=user, date=date(2026, 9, 4), weight=Decimal('40'))
    WeightEntry.objects.create(user=user, date=date(2026, 9, 5), weight=Decimal('70'))

    return user

@pytest.fixture
def api_client_with_profile(user_with_profile):
    client = APIClient()
    client.force_authenticate(user=user_with_profile)
    return client

def test_calculator_uses_manual_params_when_provided(api_client):
    """
    Проверяем, что калькулятор использует параметры, переданные вручную в запросе,
    а не пытается брать их из профиля пользователя или истории веса.
    Передаём gender, age, height, weight явно вместе с target_weight_change и days.
    Ожидаем 200 и корректный расчёт bmr/maintenance_calories/target_calories.
    """
    response = api_client.post('/api/analytics/calculator/', {
        'gender': 'male', 'age': '20', 'height': '180', 'weight': '55', 'activity_level': 'moderate',
        'target_weight_change': '5', 'days': '30'
    })
    expected = calculate_target_calories(
        gender='male', weight=Decimal('55'), height=180, age=20,
        activity_level='moderate', target_weight_change=Decimal('5'), days=30,
    )

    assert response.status_code == status.HTTP_200_OK
    assert Decimal(str(response.data['bmr'])) == expected.bmr
    assert Decimal(str(response.data['maintenance_calories'])) == expected.maintenance_calories
    assert Decimal(str(response.data['target_calories'])) == expected.target_calories

def test_calculator_returns_400_when_profile_incomplete(api_client):
    """
    Проверяем случай, когда часть данных не передана в запросе и её нет в профиле
    пользователя (например, user.height = None, user.birth_date = None),
    и при этом нет ни одной записи WeightEntry.
    Передаём только обязательные target_weight_change и days.
    Ожидаем 400 и сообщение о недостатке данных.
    """
    response = api_client.post('/api/analytics/calculator/', {
        'target_weight_change': '5', 'days': '30'
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_calculator_falls_back_to_profile_when_params_not_provided(api_client_with_profile):
    """
    Проверяем случай, когда часть данных не передана в запросе, но её можно взять из профиля
    пользователя (например, user.gender, user.height, user.birth_date),
    а вес узнаётся в последней записи WeightEntry.
    Также проверяется, что берётся последняя запись веса, а не первая/случайная
    Передаём только обязательные target_weight_change и days.
    Ожидаем 200 и корректный расчёт bmr/maintenance_calories/target_calories.
    """
    response = api_client_with_profile.post('/api/analytics/calculator/', {
        'target_weight_change': '5', 'days': '30'
    })
    expected = calculate_target_calories(
        gender='male', weight=Decimal('70'), height=180, age=20,
        activity_level='moderate', target_weight_change=Decimal('5'), days=30,
    )

    assert response.status_code == status.HTTP_200_OK
    assert Decimal(str(response.data['bmr'])) == expected.bmr
    assert Decimal(str(response.data['maintenance_calories'])) == expected.maintenance_calories
    assert Decimal(str(response.data['target_calories'])) == expected.target_calories

def test_calculator_requires_authentication(api_client_not_jwt_authentication):
    """
    Попытка воспользоваться калькулятором без jwt аутентификации.
    Ожидаем 401.
    """
    response = api_client_not_jwt_authentication.post('/api/analytics/calculator/', {
        'target_weight_change': '5', 'days': '30'
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_calculator_negative_target_weight_change_decreases_calories(api_client_with_profile):
    """
    Проверка работы калькулятора, если цель - сбросить вес.
    Ожидается 200 и точный расчёт target_calories, который также должен
    быть меньше maintenance_calories (расход снижен, а не увеличен).
    """
    response = api_client_with_profile.post('/api/analytics/calculator/', {
        'target_weight_change': '-5', 'days': '30'
    })
    expected = calculate_target_calories(
        gender='male', weight=Decimal('70'), height=180, age=20,
        activity_level='moderate', target_weight_change=Decimal('-5'), days=30,
    )

    assert response.status_code == status.HTTP_200_OK
    assert Decimal(str(response.data['target_calories'])) == expected.target_calories
    assert expected.target_calories < expected.maintenance_calories

def test_calculator_requires_target_weight_change_and_days(api_client_with_profile):
    """
    Проверяем случай, когда не передали обязательные поля.
    Ожидается 400.
    """
    response = api_client_with_profile.post('/api/analytics/calculator/', {})

    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_calculator_rejects_invalid_activity_level(api_client_with_profile):
    """
    Вводим невалидное значение choice-поля (активность пользователя).
    Ожидается 400.
    """
    response = api_client_with_profile.post('/api/analytics/calculator/', {
        'activity_level': 'wrong_name', "target_weight_change": "5", "days": "30"
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST