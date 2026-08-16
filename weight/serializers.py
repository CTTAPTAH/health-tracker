from rest_framework import serializers
from .models import WeightEntry

class WeightEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightEntry
        fields = ('id', 'date', 'weight')

    def validate(self, attrs):
        user = self.context['request'].user
        date = attrs.get('date')

        if WeightEntry.objects.filter(user=user, date=date).exists():
            raise serializers.ValidationError('Запись веса за эту дату уже существует.')

        return attrs