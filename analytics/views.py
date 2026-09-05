from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from weight.models import WeightEntry
from .serializers import CalorieCalculatorSerializer
from .services import calculate_target_calories

class CalorieCalculatorView(APIView):
    def post(self, request):
        serializer = CalorieCalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user

        gender = data.get('gender') or user.gender
        height = data.get('height') or user.height
        age = data.get('age') or self._calculate_age(user.birth_date)
        weight = data.get('weight') or self._get_latest_weight(user)
        activity_level = data.get('activity_level', 'moderate')

        if not all([gender, height, age, weight]):
            return Response(
                {'detail': 'Недостаточно данных. Заполните профиль или укажите параметры вручную.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = calculate_target_calories(
            gender=gender,
            weight=weight,
            height=height,
            age=age,
            activity_level=activity_level,
            target_weight_change=data['target_weight_change'],
            days=data['days'],
        )

        return Response({
            'bmr': result.bmr,
            'maintenance_calories': result.maintenance_calories,
            'target_calories': result.target_calories,
        })

    def _calculate_age(self, birth_date):
        if birth_date is None:
            return None

        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def _get_latest_weight(self, user):
        entry = WeightEntry.objects.filter(user=user).order_by('-date').first()
        return entry.weight if entry else None