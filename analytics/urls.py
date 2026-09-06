from django.urls import path
from .views import CalorieCalculatorView, WeightForecastView

urlpatterns = [
    path('calculator/', CalorieCalculatorView.as_view()),
    path('forecast/', WeightForecastView.as_view()),
]