# serializers.py
from rest_framework import serializers
from .models import Category, Service, Employee, Client, Appointment, Product, Review
from django.utils import timezone


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной.")
        return value


class EmployeeSerializer(serializers.ModelSerializer):
    services = serializers.StringRelatedField(many=True)

    class Meta:
        model = Employee
        fields = "__all__"


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"
        extra_kwargs = {"user": {"read_only": True}}


class AppointmentSerializer(serializers.ModelSerializer):
    client = serializers.HiddenField(default=serializers.CurrentUserDefault())
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.none(),
        required=True,
    )

    class Meta:
        model = Appointment
        fields = "__all__"
        extra_kwargs = {"status": {"read_only": True}}
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Appointment.objects.all(),
                fields=["client", "date", "time"],
                message="У клиента уже есть запись на это время",
            )
        ]

    def validate(self, attrs):
        date = attrs.get("date")
        time = attrs.get("time")
        service = attrs.get("service")
        employee = attrs.get("employee")

        # Проверка на прошлую дату+время
        if date is not None and time is not None:
            dt = timezone.datetime.combine(date, time)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            if dt < timezone.now():
                raise serializers.ValidationError(
                    {
                        "date": "Нельзя записаться на прошедшую дату и время.",
                        "time": "Нельзя записаться на прошедшую дату и время.",
                    }
                )
        if service and employee and service not in employee.services.all():
            raise serializers.ValidationError(
                {"employee": "Этот исполнитель не предоставляет выбранную услугу."}
            )

        return super().validate(attrs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        service_id = None

        if request and request.method in ("POST", "PUT", "PATCH"):
            service_id = request.data.get("service")
        elif self.instance and getattr(self.instance, "service", None):
            service_id = self.instance.service.id

        if service_id:
            self.fields["employee"].queryset = Employee.objects.filter(
                services__id=service_id
            )

    def create(self, validated_data):
        user = validated_data.pop("client")
        client = Client.objects.get(user=user)
        appointment = Appointment.objects.create(client=client, **validated_data)
        return appointment

    def update(self, instance, validated_data):
        validated_data.pop("client", None)
        return super().update(instance, validated_data)

    def get_fields(self):
        fields = super().get_fields()
        # Получаем пользователя из контекста запроса
        request = self.context.get("request")
        if request and not request.user.is_staff:
            fields["status"].read_only = True
        else:
            fields["status"].read_only = False
        return fields


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Цена продукта не может быть отрицательной."
            )
        return value


class ReviewSerializer(serializers.ModelSerializer):
    client = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # appointment инициализируем без queryset, потом зададим свой
    appointment = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.none()
    )

    class Meta:
        model = Review
        fields = ("id", "rating", "comment", "appointment", "client")
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=["appointment", "client"],
                message="Отзыв для этой записи уже оставлен",
            )
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request", None)
        if request and request.user and not request.user.is_staff:
            # Находим текущего клиента
            client = Client.objects.get(user=request.user)
            # Разрешаем выбрать только его собственные завершённые записи
            self.fields["appointment"].queryset = Appointment.objects.filter(
                client=client, status="completed"
            )
        else:
            # Админы видят любые записи
            self.fields["appointment"].queryset = Appointment.objects.all()

    def validate_appointment(self, appointment):
        request = self.context.get("request", None)
        if request and request.user and not request.user.is_staff:
            client = Client.objects.get(user=request.user)
            if appointment.client != client:
                raise serializers.ValidationError(
                    "Нельзя оставлять отзывы не к своей записи."
                )
            if appointment.status != "completed":
                raise serializers.ValidationError(
                    "Можно оставить отзыв только для выполненной записи."
                )
        return appointment

    def create(self, validated_data):
        # «client» здесь — это User, а нам нужен Client
        user = validated_data.pop("client")
        client = Client.objects.get(user=user)
        # создаём Review уже с правильным client
        return Review.objects.create(client=client, **validated_data)
