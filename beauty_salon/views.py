from django.shortcuts import render
from .models import Service, Employee, Client, Appointment, Product, Review

def home(request):
    return render(request, 'home.html')

def service_list(request):
    services = Service.objects.all()
    return render(request, 'service_list.html', {'services': services})

def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})

def client_list(request):
    clients = Client.objects.all()
    return render(request, 'client_list.html', {'clients': clients})

def appointment_list(request):
    appointments = Appointment.objects.all()
    return render(request, 'appointment_list.html', {'appointments': appointments})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

def review_list(request):
    reviews = Review.objects.all()
    return render(request, 'review_list.html', {'reviews': reviews})