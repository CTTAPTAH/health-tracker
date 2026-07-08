from django.db import models
from users.models import User

class Meal(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Завтрак'),
        ('lunch', 'Обед'),
        ('dinner', 'Ужин'),
        ('snack', 'Перекус')
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    meal_type = models.CharField(
        max_length=10,
        choices=MEAL_TYPE_CHOICES,
        verbose_name='Приём пищи'
    )
    date = models.DateField(
        verbose_name='Дата'
    )

    class Meta:
        verbose_name = 'Приём пищи'
        verbose_name_plural = 'Приёмы пищи'
        unique_together = ['user', 'date', 'meal_type']

    def __str__(self):
        return f'{self.user.username} — {self.meal_type} ({self.date})'

class MealItem(models.Model):
    meal = models.ForeignKey(
        Meal,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Приём пищи'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    is_liquid = models.BooleanField(
        default=False,
        verbose_name='Жидкость'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Масса (г/мл)'
    )
    calories = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Калорийность (на 100 г/мл)'
    )
    protein = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Белки (на 100 г/мл)'
    )
    fat = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Жиры (на 100 г/мл)'
    )
    carbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Углеводы (на 100 г/мл)'
    )

    class Meta:
        verbose_name = 'Съеденный продукт'
        verbose_name_plural = 'Съеденные продукты'

    def __str__(self):
        return f'{self.name} — {self.meal.meal_type}'

class Product(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    is_liquid = models.BooleanField(
        default=False,
        verbose_name='Жидкость'
    )
    calories = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Калорийность (на 100 г/мл)'
    )
    protein = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Белки (на 100 г/мл)'
    )
    fat = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Жиры (на 100 г/мл)'
    )
    carbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Углеводы (на 100 г/мл)'
    )

    class Meta:
        verbose_name = 'Системный продукт питания'
        verbose_name_plural = 'Системные продукты питания'

    def __str__(self):
        return self.name

class UserProduct(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    is_liquid = models.BooleanField(
        default=False,
        verbose_name='Жидкость'
    )
    calories = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Калорийность (на 100 г/мл)'
    )
    protein = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Белки (на 100 г/мл)'
    )
    fat = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Жиры (на 100 г/мл)'
    )
    carbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Углеводы (на 100 г/мл)'
    )

    class Meta:
        verbose_name = 'Пользовательский продукт питания'
        verbose_name_plural = 'Пользовательские продукты питания'

    def __str__(self):
        return f'{self.name} — {self.user.username}'