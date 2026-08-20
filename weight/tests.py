import pytest
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from weight.models import WeightEntry

@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpass123')

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
def test_create_weight_entry_success(api_client):
    """Проверка создания записи о весе. Ожидается 200"""
    response = api_client.post('/api/weight/', {
        'date': '2026-08-16',
        'weight': '75.50',
    })

    assert response.status_code == status.HTTP_201_CREATED
    assert WeightEntry.objects.count() == 1
    assert WeightEntry.objects.first().weight == 75.50

@pytest.mark.django_db
def test_create_weight_entry_duplicate_date_returns_400(api_client):
    """Создание дубликата записи о весе с одинаковой датой. Ожидается 400"""
    api_client.post('/api/weight/', {
        'date': '2026-08-16',
        'weight': '75.50',
    })

    response = api_client.post('/api/weight/', {
        'date': '2026-08-16',
        'weight': '55.45',
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert WeightEntry.objects.count() == 1
    assert WeightEntry.objects.first().weight == 75.50

@pytest.mark.django_db
def test_create_weight_entry_negative_weight_returns_400(api_client):
    """Создание записи с отрицательным весом. Ожидается 400"""
    response = api_client.post('/api/weight/', {
        'date': '2026-08-16',
        'weight': '-1.00',
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_list_weight_entries_returns_only_own_data(api_client):
    """Создание записей для двух пользователей: GET-список должен
    вернуть только записи текущего пользователя"""
    second_user = User.objects.create_user(username='testuser2', password='123')
    second_api_client = APIClient()
    second_api_client.force_authenticate(user=second_user)

    api_client.post('/api/weight/', {'date': '2026-08-16', 'weight': '75.50'})
    second_api_client.post('/api/weight/', {'date': '2026-08-17', 'weight': '45.00'})

    response = api_client.get('/api/weight/')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['weight'] == '75.50'

@pytest.mark.django_db
def test_retrieve_other_user_weight_entry_returns_404(api_client):
    """Пользователь пытается получить чужую запись веса по id. Ожидается 404"""
    second_user = User.objects.create_user(username='testuser2', password='123')
    second_api_client = APIClient()
    second_api_client.force_authenticate(user=second_user)

    second_api_client.post('/api/weight/', {
        'date': '2026-08-17', 'weight': '45.00'
    })
    other_user_entry_id = WeightEntry.objects.get(user=second_user).id

    response = api_client.get(f'/api/weight/{other_user_entry_id}/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_update_weight_entry_success(api_client):
    """Проверка на изменение значения. Ожидается 200"""
    api_client.post('/api/weight/', {
        'date': '2026-08-16',
        'weight': '75.50',
    })
    weight_entry_id = WeightEntry.objects.first().id

    response = api_client.patch(f'/api/weight/{weight_entry_id}/', {
        'weight': '60.50',
    })

    assert response.status_code == status.HTTP_200_OK
    assert WeightEntry.objects.count() == 1
    assert WeightEntry.objects.first().weight == 60.50

@pytest.mark.django_db
def test_delete_weight_entry_success(api_client):
    """Проверка на удаление записи о весе. Ожидается 204"""
    api_client.post('/api/weight/', {
        'date': '2026-08-16',
        'weight': '75.50',
    })
    weight_entry_id = WeightEntry.objects.first().id

    response = api_client.delete(f'/api/weight/{weight_entry_id}/', {})

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert WeightEntry.objects.count() == 0

@pytest.mark.django_db
def test_weight_entry_list_requires_authentication():
    """Запрос без токена и авторизации. Ожидаем 401"""
    client = APIClient()
    response = client.post('/api/weight/', {
        'date': '2026-08-16',
        'weight': '75.50',
    })

    assert response.status_code == status.HTTP_401_UNAUTHORIZED