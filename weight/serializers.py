from rest_framework import serializers
from .models import WeightEntry

class WeightEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightEntry
        fields = ('id', 'date', 'weight')
