import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from nutrition.models import Meal, MealItem, UserProduct

@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpass123')

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
def test_create_meal_with_items_success(api_client):
    """Создание Meal с вложенными items. Ожидается 201"""
    response = api_client.post('/api/nutrition/meals/', {
        'meal_type': 'dinner',
        'date': '2026-08-16',
        'items': [
            {
                'name': 'рис', 'is_liquid': False, 'amount': '300', 'calories': '300.0',
                'protein': '6.5', 'fat': '0.8', 'carbs': '79.0'
            },
            {
                'name': 'капучино', 'is_liquid': True, 'amount': '100', 'calories': '50.0',
                'protein': '2.0', 'fat': '3.5', 'carbs': '3.5'
            },
        ]
    }, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Meal.objects.count() == 1
    assert MealItem.objects.count() == 2
    assert Meal.objects.first().meal_type == 'dinner'
    assert MealItem.objects.first().name == 'рис'

@pytest.mark.django_db
def test_create_meal_duplicate_type_and_date_returns_400(api_client):
    """Создание дубликата приёма пищи. Ожидается 400"""
    api_client.post('/api/nutrition/meals/', {
        'meal_type': 'dinner',
        'date': '2026-08-16',
        'items': []
    }, format='json')

    response = api_client.post('/api/nutrition/meals/', {
        'meal_type': 'dinner',
        'date': '2026-08-16',
        'items': []
    }, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Meal.objects.count() == 1
    assert Meal.objects.first().meal_type == 'dinner'

@pytest.mark.django_db
def test_create_meal_item_with_negative_calories_returns_400(api_client):
    """Создание item с отрицательной калорийностью. Ожидается 400"""
    response = api_client.post('/api/nutrition/meals/', {
        'meal_type': 'dinner',
        'date': '2026-08-16',
        'items': [
            {
                'name': 'рис', 'is_liquid': False, 'amount': '300', 'calories': '-300.0',
                'protein': '6.5', 'fat': '0.8', 'carbs': '79.0'
            },
        ]
    }, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Meal.objects.count() == 0
    assert MealItem.objects.count() == 0

@pytest.mark.django_db
def test_create_meal_atomic_rollback_on_invalid_item(api_client):
    """Проверка транзакции: если хотя бы один item не валиден, то ничего не создаётся. Ожидается 400"""
    response = api_client.post('/api/nutrition/meals/', {
        'meal_type': 'dinner',
        'date': '2026-08-16',
        'items': [
            {
                'name': 'рис', 'is_liquid': False, 'amount': '300', 'calories': '300.0',
                'protein': '6.5', 'fat': '0.8', 'carbs': '79.0'
            },
            {
                'name': 'капучино', 'is_liquid': True, 'amount': '-100', 'calories': '50.0',
                'protein': '2.0', 'fat': '3.5', 'carbs': '3.5'
            },
        ]
    }, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Meal.objects.count() == 0
    assert MealItem.objects.count() == 0

@pytest.mark.django_db
def test_list_meals_returns_only_own_data(api_client):
    """Создание записей для двух пользователей: GET-список должен
        вернуть только записи текущего пользователя"""
    second_user = User.objects.create_user(username='testuser2', password='123')
    second_api_client = APIClient()
    second_api_client.force_authenticate(user=second_user)

    api_client.post('/api/nutrition/meals/', {
        'meal_type': 'dinner',
        'date': '2026-08-16',
        'items': []
    }, format='json')
    second_api_client.post('/api/nutrition/meals/', {
        'meal_type': 'lunch',
        'date': '2025-09-20',
        'items': []
    }, format='json')

    response = api_client.get('/api/nutrition/meals/')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['meal_type'] == 'dinner'

@pytest.mark.django_db
def test_product_list_is_read_only(api_client):
    """Проверка на то, что нельзя добавить элемент в справочник Product. Ожидается 405"""
    response = api_client.post('/api/nutrition/products/', {
        'name': 'рис', 'is_liquid': False, 'calories': '300.0',
        'protein': '6.5', 'fat': '0.8', 'carbs': '79.0'
    })

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

@pytest.mark.django_db
def test_create_user_product_success(api_client):
    """Создание продукта пользователем. Ожидается 201"""
    response = api_client.post('/api/nutrition/user-products/', {
        'name': 'рис', 'is_liquid': False, 'calories': '300.0',
        'protein': '6.5', 'fat': '0.8', 'carbs': '79.0'
    })

    assert response.status_code == status.HTTP_201_CREATED
    assert UserProduct.objects.count() == 1
    assert UserProduct.objects.first().name == 'рис'

@pytest.mark.django_db
def test_list_user_products_returns_only_own_data(api_client):
    """Создание продуктов для двух пользователей: GET-список должен
        вернуть только продукты текущего пользователя"""
    second_user = User.objects.create_user(username='testuser2', password='123')
    second_api_client = APIClient()
    second_api_client.force_authenticate(user=second_user)

    api_client.post('/api/nutrition/user-products/', {
        'name': 'рис', 'is_liquid': False, 'calories': '300.0',
        'protein': '6.5', 'fat': '0.8', 'carbs': '79.0'
    })
    second_api_client.post('/api/nutrition/user-products/', {
        'name': 'гречка', 'is_liquid': False, 'calories': '330.0',
        'protein': '12.6', 'fat': '3.3', 'carbs': '62.1'
    })

    response = api_client.get('/api/nutrition/user-products/')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['name'] == 'рис'