from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Appointment, Category, Client, Employee, Product, Review, Service

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "description", "image_url"]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной.")
        return value


class EmployeeSerializer(serializers.ModelSerializer):
    services = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

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
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    service_name = serializers.CharField(source="service.name", read_only=True)
    employee_name = serializers.CharField(source="employee.name", read_only=True)

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


class SimpleEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ("id", "name", "position")


class SimpleServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ("id", "name")


class AppointmentForReviewSerializer(serializers.ModelSerializer):
    employee = SimpleEmployeeSerializer(read_only=True)
    service = SimpleServiceSerializer(read_only=True)  # <- добавлено

    class Meta:
        model = Appointment
        fields = ("id", "date", "time", "employee", "service")


class ReviewSerializer(serializers.ModelSerializer):
    client = serializers.HiddenField(default=serializers.CurrentUserDefault())
    appointment = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.none()
    )
    appointment_details = AppointmentForReviewSerializer(
        source="appointment", read_only=True
    )
    author = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "id",
            "rating",
            "comment",
            "appointment",
            "appointment_details",
            "client",
            "author",
        )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=["appointment", "client"],
                message="Отзыв для этой записи уже оставлен",
            )
        ]
        read_only_fields = ["client", "author", "appointment_details"]

    def get_author(self, obj):
        if obj.client and obj.client.user:
            return obj.client.user.get_full_name() or obj.client.user.username
        return "Аноним"

    # Остальной код сериализатора остается без изменений
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request", None)

        if request and request.user.is_authenticated and not request.user.is_staff:
            try:
                client = Client.objects.get(user=request.user)
                self.fields["appointment"].queryset = (
                    Appointment.objects.select_related(
                        "client__user", "employee", "service"
                    ).filter(client=client, status="completed")
                )
            except Client.DoesNotExist:
                self.fields["appointment"].queryset = Appointment.objects.none()
        else:
            self.fields["appointment"].queryset = Appointment.objects.select_related(
                "client__user", "employee"
            ).all()

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
        user = self.context["request"].user
        validated_data["client"] = user.client
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "client"]

    def get_client(self, obj):
        try:
            client = Client.objects.get(user=obj)
        except Client.DoesNotExist:
            return None

        phone = getattr(client, "phone", None)
        gender = getattr(client, "gender", None)
        birth_date = getattr(client, "birth_date", None)
        photo = getattr(client, "photo", None)

        birth_date_val = birth_date.isoformat() if (birth_date is not None) else None

        request = self.context.get("request", None)
        if photo:
            try:
                photo_url = (
                    request.build_absolute_uri(photo.url)
                    if request is not None
                    else photo.url
                )
            except Exception:
                photo_url = None
        else:
            photo_url = None

        return {
            "id": client.id,
            "phone": phone,
            "gender": gender,
            "birth_date": birth_date_val,
            "photo": photo_url,
        }


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=True, allow_blank=False)
    birth_date = serializers.DateField(required=False, allow_null=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с такой почтой уже существует."
            )
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Имя пользователя уже занято.")
        return value

    def validate_phone(self, value):
        # Если хотите уникальность по телефону:
        if Client.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким телефоном уже зарегистрирован."
            )
        return value.strip()

    def validate_birth_date(self, value):
        from django.utils import timezone

        if value and value > timezone.now().date():
            raise serializers.ValidationError("Дата рождения не может быть в будущем.")
        return value

    def create(self, validated_data):
        username = validated_data["username"]
        email = validated_data["email"]
        password = validated_data["password"]
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        phone = validated_data.get("phone")
        birth_date = validated_data.get("birth_date")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        Client.objects.create(user=user, phone=phone, birth_date=birth_date)

        return user


class EmailTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError("Нужно указать email и пароль.")

        try:
            # Поиск пользователя по email, но используем username
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Неверная почта или пароль.")

        if not user.check_password(password):
            raise serializers.ValidationError("Неверная почта или пароль.")

        if not getattr(user, "is_active", True):
            raise serializers.ValidationError("Учётная запись неактивна.")

        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user, context=self.context).data,
        }
        return data
