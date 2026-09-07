from django.urls import path
from .views import (
    MealListCreateView, MealDetailView,
    ProductListView, ProductDetailView,
    UserProductListCreateView, UserProductDetailView,
    MealAIParseView
)

urlpatterns = [
    path('meals/', MealListCreateView.as_view()),
    path('meals/<int:pk>/', MealDetailView.as_view()),

    path('products/', ProductListView.as_view()),
    path('products/<int:pk>/', ProductDetailView.as_view()),

    path('user-products/', UserProductListCreateView.as_view()),
    path('user-products/<int:pk>/', UserProductDetailView.as_view()),

    path('ai-parse/', MealAIParseView.as_view()),
]