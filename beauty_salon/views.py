from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Service, Employee, Client, Appointment, Product, Review
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from .forms import ClientRegistrationForm, AppointmentForm, ReviewForm
from django.http import JsonResponse
from django.template.loader import render_to_string

def home(request):
    return render(request, 'home.html')

def service_list(request):
    categories = Category.objects.prefetch_related('services').all()
    return render(request, 'service_list.html', {'categories': categories})
def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    return render(request, 'service_detail.html', {'service': service})

def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, 'employee_detail.html', {'employee': employee})

def appointment_list(request):
    appointments = Appointment.objects.all()
    return render(request, 'appointment_list.html', {'appointments': appointments})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

def review_list(request):
    reviews = Review.objects.all()
    return render(request, 'review_list.html', {'reviews': reviews})


def register(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = ClientRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

class LogoutViewCustom(LogoutView):
    next_page = 'home'

@login_required
def profile(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return render(request, 'error.html', {
            'message': 'У вас нет профиля клиента, поэтому нет записей.'
        })

    appointments = Appointment.objects.filter(client=client).order_by('-date', '-time')

    for app in appointments:
        app.existing_review = Review.objects.filter(appointment=app).first()

    return render(request, 'profile.html', {
        'client': client,
        'appointments': appointments
    })


@login_required
def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user.client
            appointment.save()
            form.save_m2m()
            return redirect('profile')
    else:
        form = AppointmentForm(user=request.user)

    return render(request, 'appointments/create.html', {'form': form})

@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        client=request.user.client
    )
    return render(request, 'appointments/detail.html', {'appointment': appointment})

def load_employees(request):
    service_id = request.GET.get('service')
    employees = Employee.objects.filter(
        services__id=service_id
    ).distinct()
    return render(request, 'appointments/employee_dropdown.html', {'employees': employees})

@login_required
def appointment_edit(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        client=request.user.client
    )
    if appointment.status == 'completed':
        return render(request, 'error.html', {
            'message': 'Нельзя редактировать завершённую запись.'
        })

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = AppointmentForm(instance=appointment, user=request.user)

    return render(request, 'appointments/edit.html', {
        'form': form,
        'appointment': appointment
    })

@login_required
def appointment_cancel(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        client=request.user.client
    )
    if appointment.status == 'completed':
        return render(request, 'error.html', {
            'message': 'Нельзя отменить завершённую запись.'
        })

    appointment.status = 'canceled'
    appointment.save()
    return redirect('profile')


@login_required
def add_review(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user.client)

    if appointment.status != 'completed':
        return render(request, 'error.html', {"message": "Нельзя оставить отзыв для незавершённой записи."})

    if Review.objects.filter(appointment=appointment).exists():
        return render(request, 'error.html', {"message": "Отзыв уже был оставлен для этой записи."})

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appointment
            review.client = request.user.client
            review.save()

            return redirect('review_list')
    else:
        form = ReviewForm()

    return render(request, 'add_review.html', {'form': form, 'appointment': appointment})

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, client=request.user.client)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ReviewForm(instance=review)

    return render(request, 'reviews/edit_review.html', {
        'form': form,
        'review': review
    })

