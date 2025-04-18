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
    class Meta:
        model = Appointment
        fields = '__all__'
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Appointment.objects.all(),
                fields=['client', 'date', 'time'],
                message="У клиента уже есть запись на это время"
            )
        ]

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