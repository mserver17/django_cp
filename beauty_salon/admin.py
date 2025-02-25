from django.contrib import admin
from django import forms
from django.urls import path
from django.http import JsonResponse
from .models import Service, Category, Employee, Client, Appointment, Product, Review

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.service_id:  # одно поле
                self.fields['employee'].queryset = Employee.objects.filter(
                    services__id=self.instance.service_id
                ).distinct()
            else:
                self.fields['employee'].queryset = Employee.objects.none()
        else:
            self.fields['employee'].queryset = Employee.objects.none()

        if 'service' in self.data:
            try:
                service_id = int(self.data.get('service'))
                self.fields['employee'].queryset = Employee.objects.filter(
                    services__id=service_id
                ).distinct()
            except (ValueError, TypeError):
                pass
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentForm
    list_display = ('client', 'employee', 'date', 'time', 'status')
    list_editable = ('status',)
    list_filter = ('status', 'date', 'employee')
    date_hierarchy = 'date'
    raw_id_fields = ('client', 'employee')
    list_display_links = ('client', 'employee')

    class Media:
        js = ('js/admin_appointment.js',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get_employees/', self.admin_site.admin_view(self.get_employees)),
        ]
        return custom_urls + urls

    def get_employees(self, request):
        service_ids = request.GET.getlist('service_ids[]')
        employees = Employee.objects.filter(
            services__in=service_ids
        ).distinct().values('id', 'name')
        return JsonResponse(list(employees), safe=False)

class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'appointment_count')
    search_fields = ('name', 'email')
    inlines = [AppointmentInline]

    def appointment_count(self, obj):
        return obj.appointment_set.count()

    appointment_count.short_description = 'Кол-во записей'

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'position')
    filter_horizontal = ('services',)
    search_fields = ('name',)
    list_display_links = ('name', )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    list_filter = ('category', 'price')
    search_fields = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)


class StarRatingWidget(forms.RadioSelect):
    def __init__(self, attrs=None):
        choices = [(i, "⭐" * i) for i in range(1, 6)]
        super().__init__(attrs, choices)


class ReviewAdminForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = "__all__"
        widgets = {
            'rating': StarRatingWidget(),
        }


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm
    list_display = ('appointment', 'rating_display')
    list_filter = ('rating',)
    readonly_fields = ('appointment',)

    def rating_display(self, obj):
        return "⭐" * obj.rating

    rating_display.short_description = "Рейтинг"
