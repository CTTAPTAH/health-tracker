from datetime import date, timedelta
from weight.models import WeightEntry

FORECAST_WINDOW_DAYS = 14

def get_weight_entries_for_window(user, window_days=FORECAST_WINDOW_DAYS) -> list[WeightEntry]:
    """
    Возвращает записи веса пользователя за последние window_days дней,
    отсортированные по дате (по возрастанию), для построения прогноза.
    """
    cutoff_date = date.today() - timedelta(days=window_days)
    return WeightEntry.objects.filter(user=user, date__gte=cutoff_date).order_by('date')