from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    GOAL_CHOICES = [
        ('loss', 'Похудение'),
        ('gain', 'Набор массы'),
        ('maintain', 'Поддержание'),
    ]

    GENDER_CHOICES = [
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ]

    height = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Рост (см)'
    )
    goal = models.CharField(
        max_length=10,
        choices=GOAL_CHOICES,
        null=True,
        blank=True,
        verbose_name='Цель'
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        verbose_name='Пол'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username