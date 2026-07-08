from django.urls import path
from .views import WeightEntryListCreateView, WeightEntryDetailView

urlpatterns = [
    path('', WeightEntryListCreateView.as_view()),
    path('<int:pk>/', WeightEntryDetailView.as_view()),
]