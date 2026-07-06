from rest_framework import serializers
from  .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'height', 'goal', 'gender', 'birth_date')
        extra_kwargs = {
            'password': {'write_only': True}  # пароль не возвращаем в ответе
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user