# serializers.py
from rest_framework import serializers
from .models import (
    Category, Service, Employee, Client, 
    Appointment, Product, Review
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    services = serializers.StringRelatedField(many=True)
    class Meta:
        model = Employee
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True}
        }


class AppointmentSerializer(serializers.ModelSerializer):
    client = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Appointment
        fields = '__all__'
        extra_kwargs = {
            'status': {'read_only': True}  # По умолчанию запрещаем изменение
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Appointment.objects.all(),
                fields=['client', 'date', 'time'],
                message="У клиента уже есть запись на это время"
            )
        ]

    def create(self, validated_data):
        # Получаем пользователя из validated_data
        user = validated_data.pop('client')
        # Находим клиента, связанного с пользователем
        client = Client.objects.get(user=user)
        # Создаем запись с правильным клиентом
        appointment = Appointment.objects.create(client=client, **validated_data)
        return appointment

    def update(self, instance, validated_data):
        # Удаляем client из validated_data, если он случайно попал туда
        validated_data.pop('client', None)
        return super().update(instance, validated_data)

    def get_fields(self):
        fields = super().get_fields()
        # Получаем пользователя из контекста запроса
        request = self.context.get('request')
        if request and not request.user.is_staff:
            fields['status'].read_only = True  # Для клиентов
        else:
            fields['status'].read_only = False  # Для админов
        return fields

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=['appointment', 'client'],
                message="Отзыв для этой записи уже оставлен"
            )
        ]