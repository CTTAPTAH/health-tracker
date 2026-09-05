from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta

from weight.models import WeightEntry

class InsufficientDataError(Exception):
    """Вызывается, когда для регрессии имеется менее 2 точек"""
    pass

@dataclass
class DataPoint:
    x: Decimal
    y: Decimal

@dataclass
class LinearRegressionResult:
    slope: Decimal      # b - насколько меняется y на единицу x
    intercept: Decimal  # a - значение y при x = 0
    r_squared: Decimal

@dataclass
class WeightForecastPoint:
    date: date
    predicted_weight: Decimal

@dataclass
class WeightForecastResult:
    historical_fit: list[WeightForecastPoint] # линия регрессии на исторических днях
    forecast: list[WeightForecastPoint] # линия регрессии на будущих днях
    r_squared: Decimal
    confidence_level: str
    data_points_used: int

def calculate_linear_regression(points: list[DataPoint]) -> LinearRegressionResult:
    """
    Вычисляет параметры линейной регрессии методом наименьших квадратов.
    points - список DataPoint, где x и y - Decimal.
    Возвращает LinearRegressionResult(slope, intercept, r_squared).
    """
    n = len(points)
    if n < 2:
        raise InsufficientDataError(f"Нужно минимум две точки. Передано: {n}")

    n_decimal = Decimal(n)
    sum_x = Decimal('0')
    sum_y = Decimal('0')
    sum_xy = Decimal('0')
    sum_x2 = Decimal('0')

    for point in points:
        sum_x += point.x
        sum_y += point.y
        sum_xy += point.x * point.y
        sum_x2 += point.x * point.x

    slope = (n_decimal * sum_xy - sum_x * sum_y) / (n_decimal * sum_x2 - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n_decimal

    mean_y = sum_y / n_decimal
    ss_residual = Decimal('0')  # Σ(y - ŷ)²
    ss_total = Decimal('0')     # Σ(y - ȳ)²

    for point in points:
        predicted_y = intercept + slope * point.x
        ss_residual += (point.y - predicted_y) ** 2
        ss_total += (point.y - mean_y) ** 2

    # Коэффициент детерминации
    if ss_total == 0:
        # Все y одинаковы - модель идеально предсказывает данные
        r_squared = Decimal('1')
    else:
        r_squared = Decimal('1') - ss_residual / ss_total

    return LinearRegressionResult(slope=slope, intercept=intercept, r_squared=r_squared)

def get_confidence_level(r_squared: Decimal) -> str:
    """
    Переводит числовое значение R^2 в человекочитаемую категорию уверенности.
    """
    if r_squared >= Decimal('0.7'):
        return 'high'
    elif r_squared >= Decimal('0.4'):
        return 'medium'
    else:
        return 'low'

def forecast_weight(weight_entries: list[WeightEntry], days_ahead: int) -> WeightForecastResult:
    """
    Строит прогноз веса на days_ahead дней вперёд на основе истории записей.
    weight_entries - список объектов WeightEntry, отсортированных по дате
    (по возрастанию), за выбранное окно.
    Возвращает WeightForecastResult.
    """
    weight_entries = sorted(weight_entries, key=lambda e: e.date)

    first_date = weight_entries[0].date
    last_date = weight_entries[-1].date

    points = [
        DataPoint(x=Decimal((entry.date - first_date).days), y=entry.weight)
        for entry in weight_entries
    ]
    regression = calculate_linear_regression(points)

    # Линия регрессии для уже существующих значений веса
    historical_fit = [
        WeightForecastPoint(
            date=first_date + timedelta(days=int(point.x)),
            predicted_weight=round(regression.intercept + regression.slope * point.x, 2),
        )
        for point in points
    ]

    # Линия регрессии для прогноза веса
    last_x = (last_date - first_date).days
    forecast = []
    for day_offset in range(1, days_ahead + 1):
        x = Decimal(last_x + day_offset)
        predicted_weight = regression.intercept + regression.slope * x
        forecast.append(WeightForecastPoint(
            date=last_date + timedelta(days=day_offset),
            predicted_weight=round(predicted_weight, 2),
        ))

    return WeightForecastResult(
        historical_fit=historical_fit,
        forecast=forecast,
        r_squared=round(regression.r_squared, 4),
        confidence_level=get_confidence_level(regression.r_squared),
        data_points_used=len(weight_entries),
    )