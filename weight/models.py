from django.db import models
from users.models import User

class WeightEntry(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    date = models.DateField(
        verbose_name='Дата'
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Вес (кг)'
    )

    class Meta:
        verbose_name = 'Вес'
        verbose_name_plural = 'Веса'
        unique_together = ['user', 'date']

    def __str__(self):
        return f'{self.user.username} — {self.weight} кг ({self.date})'