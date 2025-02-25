from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="services", null=True, blank=True, verbose_name='Категория')
    name = models.CharField(max_length=255, verbose_name='Наименование услуги')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return self.name

class Employee(models.Model):
    name = models.CharField(max_length=100, verbose_name='ФИО')
    position = models.CharField(max_length=100, verbose_name='Специализация')
    services = models.ManyToManyField(Service, related_name='employees', verbose_name='Услуги')
    photo = models.ImageField(
        upload_to='employees/',
        null=True,
        blank=True,
        verbose_name='Фотография'
    )

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self):
        return self.name

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='ФИО')
    email = models.EmailField(unique=True, verbose_name='email')
    phone = models.CharField(max_length=15, unique=True, verbose_name='Номер телефона')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('completed', 'Выполнена'),
        ('canceled', 'Отменена'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='Клиент')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Исполнитель')
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.client.name} - {self.date} {self.time}"

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    def __str__(self):
        return self.name

class Review(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"Отзыв к записи {self.appointment}" if self.appointment else "Отзыв без привязки"