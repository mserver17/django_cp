from django import forms
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.utils.safestring import mark_safe
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
from import_export.widgets import ForeignKeyWidget
from simple_history.admin import SimpleHistoryAdmin

from .models import Appointment, Category, Client, Employee, Product, Review, Service


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.service_id:  # одно поле
                self.fields["employee"].queryset = Employee.objects.filter(
                    services__id=self.instance.service_id
                ).distinct()
            else:
                self.fields["employee"].queryset = Employee.objects.none()
        else:
            self.fields["employee"].queryset = Employee.objects.none()

        if "service" in self.data:
            try:
                service_id = int(self.data.get("service"))
                self.fields["employee"].queryset = Employee.objects.filter(
                    services__id=service_id
                ).distinct()
            except (ValueError, TypeError):
                pass


# Ресурс для экспорта записей
class AppointmentResource(resources.ModelResource):
    client_name = fields.Field(attribute="client__name", column_name="Клиент")
    service_name = fields.Field(attribute="service__name", column_name="Услуга")
    status_display = fields.Field(
        column_name="Статус", widget=ForeignKeyWidget(Appointment, "get_status_display")
    )

    class Meta:
        model = Appointment
        fields = ("id", "client_name", "service_name", "date", "time", "status_display")
        export_order = (
            "id",
            "client_name",
            "service_name",
            "date",
            "time",
            "status_display",
        )
        verbose_name_plural = "Записи"

    def get_export_queryset(self):
        """Фильтрация: исключаем отмененные записи"""
        return super().get_export_queryset().exclude(status="canceled")


@admin.register(Appointment)
class AppointmentAdmin(SimpleHistoryAdmin, ImportExportModelAdmin):
    resource_class = AppointmentResource
    form = AppointmentForm
    list_display = ("client", "employee", "date", "time", "status")
    history_list_display = ["status"]
    list_editable = ("status",)
    list_filter = ("status", "date", "employee")
    date_hierarchy = "date"
    raw_id_fields = ("client", "employee")
    list_display_links = ("client", "employee")
    formats = [base_formats.XLS, base_formats.XLSX, base_formats.CSV]

    class Media:
        js = ("js/admin_appointment.js",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("get_employees/", self.admin_site.admin_view(self.get_employees)),
        ]
        return custom_urls + urls

    def get_employees(self, request):
        service_ids = request.GET.getlist("service_ids[]")
        employees = (
            Employee.objects.filter(services__in=service_ids)
            .distinct()
            .values("id", "name")
        )
        return JsonResponse(list(employees), safe=False)


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    list_display = ("name", "email", "phone", "appointment_count")
    search_fields = ("name", "email")
    inlines = [AppointmentInline]

    def appointment_count(self, obj):
        return obj.appointment_set.count()

    appointment_count.short_description = "Кол-во записей"


@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    list_display = ("id", "name", "position")
    filter_horizontal = ("services",)
    search_fields = ("name",)
    list_display_links = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "image_preview"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, "url"):
            try:
                img_html = (
                    f'<img src="{obj.image.url}" '
                    'width="100" height="100" style="object-fit: cover;" />'
                )
                return mark_safe(img_html)
            except ValueError:
                return "Файл поврежден"
        return "Нет изображения"

    image_preview.short_description = "Превью изображения"


@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin):
    list_display = ("name", "category", "price")
    list_filter = ("category", "price")
    search_fields = ("name", "description")


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    list_display = ("name", "price")
    search_fields = ("name",)


class StarRatingWidget(forms.RadioSelect):
    def __init__(self, attrs=None):
        choices = [(i, "⭐" * i) for i in range(1, 6)]
        super().__init__(attrs, choices)


class ReviewAdminForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = "__all__"
        widgets = {
            "rating": StarRatingWidget(),
        }


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm
    list_display = ("appointment", "rating_display")
    list_filter = ("rating",)
    readonly_fields = [
        "appointment",
        "client",
        "rating",
        "comment",
    ]

    def has_add_permission(self, request):
        # Запретить админам создавать отзывы через админку
        return False

    def rating_display(self, obj):
        return "⭐" * obj.rating

    rating_display.short_description = "Рейтинг"
