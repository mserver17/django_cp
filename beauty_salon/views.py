from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

# DRF imports
from rest_framework import filters
from rest_framework import permissions
from rest_framework import permissions as drf_permissions
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

# Cache imports
from django.core.cache import cache
from .cache_utils import get_cached_data
from .decorators import cache_per_user
from django.utils.decorators import method_decorator

from .forms import AppointmentForm, ClientRegistrationForm, ReviewForm
from .models import Appointment, Category, Client, Employee, Product, Review, Service
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .serializers import (
    AppointmentSerializer,
    CategorySerializer,
    ClientSerializer,
    EmailTokenObtainPairSerializer,
    EmployeeSerializer,
    ProductSerializer,
    RegisterSerializer,
    ReviewSerializer,
    ServiceSerializer,
    UserSerializer,
)


def home(request):
    return render(request, "home.html")


def service_list(request):
    categories = Category.objects.prefetch_related("services").all()
    return render(request, "service_list.html", {"categories": categories})


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    return render(request, "service_detail.html", {"service": service})


def employee_list(request):
    employees = Employee.objects.all()
    return render(request, "employee_list.html", {"employees": employees})


def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, "employee_detail.html", {"employee": employee})


def appointment_list(request):
    appointments = Appointment.objects.all()
    return render(request, "appointment_list.html", {"appointments": appointments})


def product_list(request):
    products = Product.objects.all()
    return render(request, "product_list.html", {"products": products})


def review_list(request):
    reviews = Review.objects.all()
    return render(request, "review_list.html", {"reviews": reviews})


def register(request):
    if request.method == "POST":
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = ClientRegistrationForm()
    return render(request, "registration/register.html", {"form": form})


class LogoutViewCustom(LogoutView):
    next_page = "home"


@login_required
def profile(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return render(
            request,
            "error.html",
            {"message": "У вас нет профиля клиента, поэтому нет записей."},
        )

    appointments = Appointment.objects.filter(client=client).order_by("-date", "-time")

    for app in appointments:
        app.existing_review = Review.objects.filter(appointment=app).first()

    return render(
        request, "profile.html", {"client": client, "appointments": appointments}
    )


@login_required
def appointment_create(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user.client
            appointment.save()
            form.save_m2m()
            return redirect("profile")
    else:
        form = AppointmentForm(user=request.user)

    return render(request, "appointments/create.html", {"form": form})


@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(
        Appointment, id=appointment_id, client=request.user.client
    )
    return render(request, "appointments/detail.html", {"appointment": appointment})


def load_employees(request):
    service_id = request.GET.get("service")
    employees = Employee.objects.filter(services__id=service_id).distinct()
    return render(
        request, "appointments/employee_dropdown.html", {"employees": employees}
    )


@login_required
def appointment_edit(request, appointment_id):
    appointment = get_object_or_404(
        Appointment, id=appointment_id, client=request.user.client
    )
    if appointment.status == "completed":
        return render(
            request,
            "error.html",
            {"message": "Нельзя редактировать завершённую запись."},
        )

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = AppointmentForm(instance=appointment, user=request.user)

    return render(
        request, "appointments/edit.html", {"form": form, "appointment": appointment}
    )


@login_required
def appointment_cancel(request, appointment_id):
    appointment = get_object_or_404(
        Appointment, id=appointment_id, client=request.user.client
    )
    if appointment.status == "completed":
        return render(
            request, "error.html", {"message": "Нельзя отменить завершённую запись."}
        )

    appointment.status = "canceled"
    appointment.save()
    return redirect("profile")


@login_required
def add_review(request, appointment_id):
    appointment = get_object_or_404(
        Appointment, id=appointment_id, client=request.user.client
    )

    if appointment.status != "completed":
        return render(
            request,
            "error.html",
            {"message": "Нельзя оставить отзыв для незавершённой записи."},
        )

    if Review.objects.filter(appointment=appointment).exists():
        return render(
            request,
            "error.html",
            {"message": "Отзыв уже был оставлен для этой записи."},
        )

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appointment
            review.client = request.user.client
            review.save()

            return redirect("review_list")
    else:
        form = ReviewForm()

    return render(
        request, "add_review.html", {"form": form, "appointment": appointment}
    )


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, client=request.user.client)

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ReviewForm(instance=review)

    return render(request, "reviews/edit_review.html", {"form": form, "review": review})


# ================== Классы для DRF API ==================


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()

        cache_key = "categories_all"
        return get_cached_data(cache_key, lambda: Category.objects.all(), 60 * 60)


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filterset_fields = ["category", "price"]
    search_fields = ["name", "description"]
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Service.objects.none()

        cache_key = "services_all"
        return get_cached_data(
            cache_key, lambda: Service.objects.all(), 60 * 30  # 30 минут для услуг
        )


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    search_fields = ["name", "position"]
    filterset_fields = ["position", "services"]
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Employee.objects.none()

        cache_key = "employees_all"
        return get_cached_data(cache_key, lambda: Employee.objects.all(), 60 * 30)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_fields = ["category", "price"]
    search_fields = ["name"]
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()

        cache_key = "products_all"
        return get_cached_data(
            cache_key, lambda: Product.objects.all(), 60 * 30  # 30 минут для продуктов
        )


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "email"]
    permission_classes = [IsAdminUser]


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filterset_fields = ["status", "service", "employee"]
    search_fields = ["client__name", "service__name"]
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        # Для генерации схемы Swagger возвращаем пустой queryset
        if getattr(self, "swagger_fake_view", False):
            return Appointment.objects.none()

        # Проверяем, аутентифицирован ли пользователь
        if not self.request.user.is_authenticated:
            return Appointment.objects.none()

        if self.request.user.is_staff:
            queryset = Appointment.objects.all()
        else:
            try:
                queryset = Appointment.objects.filter(client__user=self.request.user)
            except (AttributeError, ValueError):
                return Appointment.objects.none()

        date = self.request.query_params.get("date")
        service = self.request.query_params.get("service")

        if date and service:
            queryset = queryset.filter(
                Q(date=date) & Q(service__id=service) & ~Q(status="canceled")
            )
        return queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        mutable_data = request.data.copy()

        if not request.user.is_staff:
            mutable_data.pop("status", None)

        serializer = self.get_serializer(
            instance, data=mutable_data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def get_serializer_context(self):
        return {"request": self.request}

    @action(detail=False, methods=["get"])
    def urgent(self, request):
        from django.utils import timezone

        queryset = self.get_queryset().filter(
            Q(date=timezone.now().date()) & Q(status="pending")
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = "confirmed"
        appointment.save()
        return Response({"status": "confirmed"})

    @method_decorator(cache_per_user(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_per_user(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@method_decorator(cache_per_user(60 * 15), name="list")
@method_decorator(cache_per_user(60 * 15), name="retrieve")
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related(
        "appointment",
        "appointment__employee",
        "appointment__service",
        "client",
        "client__user",
    ).all()
    serializer_class = ReviewSerializer
    pagination_class = None

    def get_queryset(self):
        return super().get_queryset()

    @action(detail=False, methods=["get"])
    def high_rating(self, request):
        queryset = self.get_queryset().filter(rating__gte=4)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        client = self.request.user.client
        appointment = serializer.validated_data.get("appointment")

        if appointment.status != "completed":
            raise ValidationError("Приём не завершён.")

        if appointment.client != client:
            raise PermissionDenied("Вы не можете оставить отзыв к чужой записи.")

        serializer.save(client=client)

    def perform_update(self, serializer):
        if "client" in serializer.validated_data:
            raise PermissionDenied("Нельзя изменять клиента отзыва.")
        serializer.save()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]


class UserReviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.select_related(
            "appointment",
            "appointment__employee",
            "appointment__service",
            "client",
            "client__user",
        ).filter(client__user=self.request.user)


# ================== Доп. API View ==================
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)


class RegisterAPIView(APIView):
    permission_classes = [drf_permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"detail": "Пользователь создан"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


# ================== Регистрация роутера для DRF API ==================
router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"services", ServiceViewSet)
router.register(r"employees", EmployeeViewSet)
router.register(r"clients", ClientViewSet)
router.register(r"appointments", AppointmentViewSet)
router.register(r"products", ProductViewSet)
router.register(r"reviews", ReviewViewSet)
router.register(r"my-reviews", UserReviewViewSet, basename="my-review")
