# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Client, Appointment, Service, Employee, Review
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils import timezone


class AppointmentForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        label="Услуга",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        label="Мастер",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Дата",
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        label="Время",
    )

    class Meta:
        model = Appointment
        fields = ["service", "employee", "date", "time"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields["employee"].queryset = Employee.objects.none()

            if self.instance and self.instance.pk and "service" not in self.data:
                service_id = self.instance.service_id
                if service_id:
                    self.fields["employee"].queryset = Employee.objects.filter(
                        services__id=service_id
                    ).distinct()

            elif "service" in self.data:
                try:
                    service_id = int(self.data.get("service"))
                    self.fields["employee"].queryset = Employee.objects.filter(
                        services__id=service_id
                    ).distinct()
                except (ValueError, TypeError):
                    pass
            else:
                self.fields["employee"].queryset = Employee.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")

        if date and time:
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(date, time)
            )
            if appointment_datetime < timezone.now():
                raise ValidationError("Нельзя записаться на прошедшую дату и время.")

        return cleaned_data


class ClientRegistrationForm(UserCreationForm):
    phone = forms.CharField(
        min_length=10,
        max_length=20,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "+7 (---) --- -- --",
                "id": "phone",
            }
        ),
    )
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label="Имя",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Введите ваше имя"}
        ),
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        label="Фамилия",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Введите вашу фамилию"}
        ),
    )
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Введите имя пользователя"}
        )
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Введите ваш email"}
        )
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Подтвердите пароль"}
        )
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
            "phone",
            "birth_date",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            Client.objects.create(
                user=user,
                phone=self.cleaned_data["phone"],
                birth_date=self.cleaned_data["birth_date"],
                name=f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}",
                email=self.cleaned_data["email"],
            )
            user.groups.add(Group.objects.get(name="Clients"))
        return user


class StarRatingWidget(forms.RadioSelect):
    def __init__(self, attrs=None):
        choices = [(i, "⭐" * i) for i in range(1, 6)]
        super().__init__(attrs, choices)


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": StarRatingWidget(),
        }
        labels = {
            "rating": "Оценка",
            "comment": "Комментарий",
        }
