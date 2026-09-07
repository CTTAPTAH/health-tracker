import pytest
from unittest.mock import patch
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from nutrition.services.ai_meal_parser import ParsedMealItem, MealParsingError

pytestmark = pytest.mark.django_db
target_patch = 'nutrition.views.parse_meal_description'

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpass123')

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

def test_ai_parse_returns_200_with_serialized_items(api_client):
    """
    Проверяем happy path: parse_meal_description возвращает список ParsedMealItem,
    view должен вернуть 200 и корректно сериализованный список items в ответе
    (проверить структуру и значения хотя бы одного item).
    """
    fake_items = [
        ParsedMealItem(
            name="Банан", is_liquid=False, amount=Decimal('118'),
            calories=Decimal('105'), protein=Decimal('1.3'), fat=Decimal('0.3'), carbs=Decimal('27.0')
        )
    ]

    with patch(target_patch, return_value=fake_items) as mocked_parse:
        response = api_client.post('/api/nutrition/ai-parse/', {
            'description': 'банан'
        })

    assert response.status_code == status.HTTP_200_OK
    assert mocked_parse.call_count == 1
    assert len(response.data['items']) == 1
    assert response.data['items'][0]['name'] == 'Банан'

def test_ai_parse_returns_422_when_no_items_recognized(api_client):
    """
    Проверяем случай, когда parse_meal_description вернул пустой список
    (описание не похоже на еду). Ожидаем 422 и сообщение в detail.
    """
    fake_items = []

    with patch(target_patch, return_value=fake_items) as mocked_parse:
        response = api_client.post('/api/nutrition/ai-parse/', {
            'description': 'банан'
        })

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.data['detail'] is not None
    assert mocked_parse.call_count == 1

def test_ai_parse_returns_502_when_parsing_fails(api_client):
    """
    Проверяем случай, когда parse_meal_description выбрасывает MealParsingError
    (не удалось получить валидный JSON после всех попыток). Ожидаем 502.
    """
    with patch(target_patch, side_effect=MealParsingError("Не удалось распарсить JSON")) as mocked_parse:
        response = api_client.post('/api/nutrition/ai-parse/', {
            'description': 'банан'
        })

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert response.data['detail'] is not None
    assert mocked_parse.call_count == 1

def test_ai_parse_returns_400_for_too_short_description(api_client):
    """
    Проверяем валидацию сериализатора: описание короче min_length (например,
    2 символа). Ожидаем 400, при этом parse_meal_description не должен
    быть вызван вообще (можно проверить через mock.assert_not_called()).
    """
    fake_items = []

    with patch(target_patch, return_value=fake_items) as mocked_parse:
        response = api_client.post('/api/nutrition/ai-parse/', {
            'description': 'ба'
        })

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mocked_parse.assert_not_called()

def test_ai_parse_returns_400_for_missing_description(api_client):
    """
    Проверяем, что запрос без поля description вообще отклоняется с 400.
    """
    fake_items = []

    with patch(target_patch, return_value=fake_items) as mocked_parse:
        response = api_client.post('/api/nutrition/ai-parse/', {})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mocked_parse.assert_not_called()

def test_ai_parse_requires_authentication():
    """
    Проверяем, что без JWT-аутентификации запрос возвращает 401.
    """
    client = APIClient()
    response = client.post('/api/nutrition/ai-parse/', {})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED