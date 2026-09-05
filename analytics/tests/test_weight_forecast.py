import pytest
from datetime import date, timedelta
from decimal import Decimal

from users.models import User
from weight.models import WeightEntry
from analytics.services.weight_forecast import (InsufficientDataError, DataPoint,
                                                calculate_linear_regression, get_confidence_level,
                                                forecast_weight)

# Тесты calculate_linear_regression
def test_calculate_linear_regression_with_perfect_linear_data():
    """
    Проверяем регрессию на идеально линейных данных (вес растёт ровно на 1 кг в день).
    Ожидаем slope = 1, intercept = вес в день x=0, r_squared = 1 (без единой ошибки).
    """
    points = [DataPoint(x=Decimal(num), y=Decimal(num)) for num in range(0, 10)]
    result = calculate_linear_regression(points)

    assert result.slope == Decimal(1)
    assert result.intercept == Decimal(0)
    assert result.r_squared == Decimal(1)

def test_calculate_linear_regression_with_constant_weight():
    """
    Проверяем случай, когда вес не меняется вообще (все y одинаковые).
    Ожидаем slope = 0. r_squared = 1 (когда все y одинаковы,
    модель идеально предсказывает данные)
    """
    points = [DataPoint(x=Decimal(num), y=Decimal(10)) for num in range(0, 10)]
    result = calculate_linear_regression(points)

    assert result.slope == Decimal(0)
    assert result.r_squared == Decimal(1)

def test_calculate_linear_regression_with_decreasing_weight():
    """
    Проверяем регрессию на данных с чётким падением веса (например, -1 кг в день).
    Ожидаем отрицательный slope и r_squared, близкий к 1 (данные линейные).
    """
    points = [DataPoint(x=Decimal(num), y=Decimal(11 - num)) for num in range(10)]
    result = calculate_linear_regression(points)

    assert result.slope < Decimal(0)
    assert result.r_squared == Decimal(1)

def test_calculate_linear_regression_with_noisy_data():
    """
    Проверяем регрессию на данных, которые в целом растут, но не идеально линейно
    (есть небольшие отклонения от прямой день ко дню).
    Ожидаем r_squared строго меньше 1, но больше 0 - линия объясняет тренд не идеально,
    но лучше, чем просто среднее.
    """
    points = [
        DataPoint(x=Decimal(1), y=Decimal(1)),
        DataPoint(x=Decimal(13), y=Decimal(5)),
        DataPoint(x=Decimal(15), y=Decimal(25)),
        DataPoint(x=Decimal(43), y=Decimal(28)),
        DataPoint(x=Decimal(50), y=Decimal(44)),
    ]
    result = calculate_linear_regression(points)
    assert Decimal(0) < result.r_squared < Decimal(1)

def test_calculate_linear_regression_raises_error_with_single_point():
    """
    Проверяем защиту от недостаточного количества точек (n = 1).
    Ожидаем InsufficientDataError.
    """
    points = [DataPoint(x=Decimal(1), y=Decimal(1)),]

    with pytest.raises(InsufficientDataError):
        calculate_linear_regression(points)

def test_calculate_linear_regression_raises_error_with_no_points():
    """
    Проверяем защиту от пустого списка точек (n = 0).
    Ожидаем InsufficientDataError.
    """
    points = []

    with pytest.raises(InsufficientDataError):
        calculate_linear_regression(points)

# Тесты get_confidence_level
def test_get_confidence_level_returns_high_for_high_r_squared():
    """
    Проверяем, что r_squared >= 0.7 даёт уровень 'high'.
    Также проверяем, что граничное значение ровно 0.7 отдельно.
    """
    result = get_confidence_level(Decimal('0.8'))
    assert result == 'high'

    borderline_result = get_confidence_level(Decimal('0.7'))
    assert borderline_result == 'high'

def test_get_confidence_level_returns_medium_for_medium_r_squared():
    """
    Проверяем, что r_squared в диапазоне [0.4, 0.7) даёт уровень 'medium'.
    Также проверяем граничное значение ровно 0.4 отдельно.
    """
    result = get_confidence_level(Decimal('0.5'))
    assert result == 'medium'

    borderline_result = get_confidence_level(Decimal('0.4'))
    assert borderline_result == 'medium'

def test_get_confidence_level_returns_low_for_low_r_squared():
    """
    Проверяем, что r_squared < 0.4 даёт уровень 'low'.
    Также проверяем случай отрицательного r_squared (плохая регрессия).
    """
    result = get_confidence_level(Decimal('0.2'))
    assert result == 'low'

    borderline_result = get_confidence_level(Decimal('-0.1'))
    assert borderline_result == 'low'

# Тесты forecast_weight
@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpass123')

def test_forecast_weight_returns_correct_number_of_forecast_points(user):
    """
    Проверяем, что при запросе прогноза на N дней вперёд массив forecast
    содержит ровно N точек, а не больше и не меньше.
    """
    count_entries = 10
    days_ahead = 5
    entries = [WeightEntry(
        user=user,
        date=date.today() - timedelta(days=count_entries - num),
        weight=Decimal(num)
    ) for num in range(count_entries)]

    result = forecast_weight(entries, days_ahead)

    assert len(result.forecast) == days_ahead

def test_forecast_weight_returns_correct_number_of_historical_fit_points(user):
    """
    Проверяем, что historical_fit содержит ровно столько точек, сколько было
    передано исходных записей веса (по одной fitted-точке на каждую реальную).
    """
    count_entries = 10
    entries = [WeightEntry(
        user=user,
        date=date.today() - timedelta(days=count_entries - num),
        weight=Decimal(num)
    ) for num in range(count_entries)]

    result = forecast_weight(entries, 5)

    assert len(result.historical_fit) == count_entries

def test_forecast_weight_forecast_dates_are_sequential_after_last_entry(user):
    """
    Проверяем, что даты в forecast идут по порядку, начиная со дня, следующего
    сразу после последней даты в weight_entries (без пропусков и без повтора
    последней известной даты).
    """
    count_entries = 10
    days_ahead = 3
    entries = [WeightEntry(
        user=user,
        date=date.today() - timedelta(days=count_entries - num),
        weight=Decimal(num)
    ) for num in range(count_entries)]

    result = forecast_weight(entries, days_ahead)

    assert len(result.forecast) == days_ahead
    assert result.forecast[0].date == date.today()
    assert result.forecast[1].date == date.today() + timedelta(days=1)
    assert result.forecast[2].date == date.today() + timedelta(days=2)

def test_forecast_weight_with_unsorted_entries_gives_same_result_as_sorted(user):
    """
    Проверяем, что функция не чувствительна к порядку элементов на входе:
    передаём weight_entries в перемешанном порядке и сравниваем результат
    с результатом на тех же данных, но заранее отсортированных.
    """
    count_entries = 10
    entries = [WeightEntry(
        user=user,
        date=date.today() - timedelta(days=count_entries - num),
        weight=Decimal(num)
    ) for num in range(count_entries)]

    sorted_entries = sorted(entries, key=lambda e: e.date)

    shuffled_entries = entries.copy()
    shuffled_entries[2], shuffled_entries[8] = shuffled_entries[8], shuffled_entries[2]

    result_from_sorted = forecast_weight(sorted_entries, 3)
    result_from_shuffled = forecast_weight(shuffled_entries, 3)

    assert result_from_sorted == result_from_shuffled

def test_forecast_weight_predicts_continued_trend_for_linear_data(user):
    """
    Проверяем на идеально линейных данных (например, +1 кг в день за 10 дней),
    что прогнозные значения в forecast продолжают тот же тренд с той же скоростью
    (можно проверить конкретное ожидаемое значение на день N вперёд, посчитав вручную).
    """
    count_entries = 10
    days_ahead = 3
    entries = [WeightEntry(
        user=user,
        date=date.today() - timedelta(days=count_entries - num),
        weight=Decimal(num)
    ) for num in range(count_entries)]

    result = forecast_weight(entries, days_ahead)

    assert result.forecast[0].predicted_weight == 10
    assert result.forecast[1].predicted_weight == 11
    assert result.forecast[2].predicted_weight == 12

def test_forecast_weight_raises_error_with_insufficient_entries(user):
    """
    Проверяем, что функция кидает InsufficientDataError, если передано
    меньше двух записей веса (см. поведение calculate_linear_regression).
    """
    entries = [WeightEntry(user=user, date=date.today(), weight=Decimal(20))]

    with pytest.raises(InsufficientDataError):
        forecast_weight(entries, 3)