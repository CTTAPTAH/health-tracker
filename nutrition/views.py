from rest_framework.generics import ListAPIView, RetrieveAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Meal, Product, UserProduct
from .serializers import MealSerializer, ProductSerializer, UserProductSerializer

# Приём пищи + питание
class MealListCreateView(ListCreateAPIView):
    serializer_class = MealSerializer

    def get_queryset(self):
        return Meal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MealDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MealSerializer

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
    serializer_class = UserProductSerializer

    def get_queryset(self):
        return UserProduct.objects.filter(user=self.request.user)