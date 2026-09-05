from dataclasses import dataclass
from decimal import Decimal

@dataclass
class CalorieCalculationResult:
    bmr: Decimal
    maintenance_calories: Decimal
    target_calories: Decimal

ACTIVITY_COEFFICIENTS = {
    'sedentary': Decimal('1.2'),
    'light': Decimal('1.375'),
    'moderate': Decimal('1.55'),
    'active': Decimal('1.725'),
    'very_active': Decimal('1.9'),
}

CALORIES_PER_KG = Decimal('7700')

def calculate_bmr(gender, weight, height, age):
    """Базовый метаболизм по формуле Mifflin-St Jeor"""
    base = Decimal('10') * weight + Decimal('6.25') * height - Decimal('5') * age

    if gender == 'male':
        return base + Decimal('5')

    return base - Decimal('161')

def calculate_tdee(bmr, activity_level):
    """Суточная норма калорий с учётом активности"""
    coefficient = ACTIVITY_COEFFICIENTS[activity_level]
    return bmr * coefficient

def calculate_target_calories(gender, weight, height, age, activity_level, target_weight_change, days):
    """Итоговая рекомендуемая калорийность в день для достижения цели"""
    bmr = calculate_bmr(gender, weight, height, age)
    tdee = calculate_tdee(bmr, activity_level)

    total_calories_needed = target_weight_change * CALORIES_PER_KG
    daily_adjustment = total_calories_needed / days
    target_calories = tdee + daily_adjustment

    return CalorieCalculationResult(
        bmr=round(bmr, 2),
        maintenance_calories=round(tdee, 2),
        target_calories=round(target_calories, 2),
    )