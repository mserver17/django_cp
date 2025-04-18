# beauty_salon/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import add_review, edit_review

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.service_list, name='service_list'),
    path('services/<int:service_id>/', views.service_detail, name='service_detail'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employee/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('profile/', views.profile, name='profile'),

    # path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointment/create/', views.appointment_create, name='appointment_create'),
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<int:appointment_id>/edit/', views.appointment_edit, name='appointment_edit'),
    path('appointment/<int:appointment_id>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    path('ajax/load-employees/', views.load_employees, name='ajax_load_employees'),

    path('products/', views.product_list, name='product_list'),
    path('reviews/', views.review_list, name='review_list'),
    path('review/<int:review_id>/edit/', edit_review, name='edit_review'),
    path('appointment/<int:appointment_id>/add_review/', add_review, name='add_review'),
    path('register/', views.register, name='register'),

]