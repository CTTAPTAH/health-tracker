from django.urls import path
from .views import CalorieCalculatorView

urlpatterns = [
    path('calculator/', CalorieCalculatorView.as_view()),
]