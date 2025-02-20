# beauty_salon/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.service_list, name='service_list'),
    path('employees/', views.employee_list, name='employee_list'),
    path('clients/', views.client_list, name='client_list'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('products/', views.product_list, name='product_list'),
    path('reviews/', views.review_list, name='review_list'),
]