from rest_framework import serializers

class CalorieCalculatorSerializer(serializers.Serializer):
    GENDER_CHOICES = [
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ]

    ACTIVITY_CHOICES = [
        ('sedentary', 'Сидячий образ жизни'),
        ('light', 'Лёгкая активность (1-3 тренировки/нед)'),
        ('moderate', 'Умеренная активность (3-5 тренировок/нед)'),
        ('active', 'Высокая активность (6-7 тренировок/нед)'),
        ('very_active', 'Очень высокая активность (физ. работа + спорт)'),
    ]

    gender = serializers.ChoiceField(choices=GENDER_CHOICES, required=False)
    age = serializers.IntegerField(min_value=1, max_value=120, required=False)
    height = serializers.IntegerField(min_value=1, required=False)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    activity_level = serializers.ChoiceField(choices=ACTIVITY_CHOICES, required=False)
    target_weight_change = serializers.DecimalField(max_digits=5, decimal_places=2)
    days = serializers.IntegerField(min_value=1)

class WeightForecastSerializer(serializers.Serializer):
    days_ahead = serializers.IntegerField(min_value=1, max_value=30, required=False, default=14)