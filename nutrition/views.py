from rest_framework.generics import ListAPIView, RetrieveAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from typing import Any

from users.permissions import IsOwner
from .models import Meal, Product, UserProduct
from .serializers import MealSerializer, ProductSerializer, UserProductSerializer, MealAIParseSerializer
from .services.ai_meal_parser import parse_meal_description, MealParsingError

# Приём пищи + питание
class MealListCreateView(ListCreateAPIView):
    serializer_class = MealSerializer

    def get_queryset(self):
        return Meal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MealDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MealSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Meal.objects.filter(user=self.request.user)

# Системный продукт
class ProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# Пользовательский продукт
class UserProductListCreateView(ListCreateAPIView):
    serializer_class = UserProductSerializer

    def get_queryset(self):
        return UserProduct.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserProductDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = UserProductSerializer

    def get_queryset(self):
        return UserProduct.objects.filter(user=self.request.user)

# Запрос ИИ
class MealAIParseView(APIView):
    def post(self, request):
        serializer = MealAIParseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            items = parse_meal_description(data['description'])
        except MealParsingError:
            return Response(
                {'detail': 'Не удалось распознать описание. Попробуйте переформулировать или введите вручную.'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if not items:
            return Response(
                {'detail': 'Не удалось распознать еду в описании. Попробуйте переформулировать или введите вручную.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        return Response({
            'items': self._serialize_items(items)
        })

    @staticmethod
    def _serialize_items(items) -> list[dict[str, Any]]:
        return [
            {
                'name': item.name,
                'is_liquid': item.is_liquid,
                'amount': item.amount,
                'calories': item.calories,
                'protein': item.protein,
                'fat': item.fat,
                'carbs': item.carbs,
            }
            for item in items
        ]