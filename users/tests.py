from http.client import responses

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User

@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpass123')

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
def test_register_user_success():
    """Проверка регистрации пользователя. Ожидается 201"""
    client = APIClient()
    response = client.post('/api/users/register/', {
        'username': 'newuser', 'email': 'newuser@gmail.com', 'password': 'Pass_1234',
    })

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.count() == 1

@pytest.mark.django_db
def test_register_user_duplicate_username_returns_400(user):
    """Регистрация дубликата пользователя. Ожидается 400"""
    client = APIClient()
    response = client.post('/api/users/register/', {
        'username': user.username, 'email': 'another@gmail.com', 'password': 'Pass_1234',
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.count() == 1

@pytest.mark.django_db
def test_obtain_token_success(user):
    """Проверка получения токена. Ожидается 200"""
    client = APIClient()
    response = client.post('/api/token/', {
        'username': user.username, 'password': 'testpass123'
    })

    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
    assert 'refresh' in response.data

@pytest.mark.django_db
def test_obtain_token_wrong_password_returns_401(user):
    """Пользователь ввёл неверный пароль и пытается получить токен. Ожидается 401"""
    client = APIClient()
    response = client.post('/api/token/', {
        'username': user.username, 'password': 'wrong_password'
    })

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_profile_view_returns_current_user_data(api_client):
    """Получение данных пользователя. Ожидается 200"""
    response = api_client.get('/api/users/profile/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['username'] == 'testuser'

@pytest.mark.django_db
def test_profile_view_requires_authentication():
    """Получение данных пользователя без авторизации. Ожидается 401"""
    client = APIClient()
    response = client.get('/api/users/profile/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED