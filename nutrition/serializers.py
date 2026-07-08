from rest_framework import serializers
from django.db import transaction
from .models import Meal, MealItem, Product, UserProduct

class MealItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealItem
        fields = ('id', 'name', 'is_liquid', 'amount', 'calories', 'protein', 'fat', 'carbs')

class MealSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True)

    class Meta:
        model = Meal
        fields = ('id', 'meal_type', 'date', 'items')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        with transaction.atomic():
            meal = Meal.objects.create(**validated_data)
            for item_data in items_data:
                MealItem.objects.create(meal=meal, **item_data)
        return meal

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'is_liquid', 'calories', 'protein', 'fat', 'carbs')

class UserProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProduct
        fields = ('id', 'name', 'is_liquid', 'calories', 'protein', 'fat', 'carbs')