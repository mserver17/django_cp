from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from .models import Appointment

@shared_task
def delete_old_appointments():
    """
    Удаляет записи (Appointment), созданные более 1 года назад.
    """
    cutoff = timezone.now() - timezone.timedelta(days=365)
    qs = Appointment.objects.filter(created_at__lt=cutoff)
    deleted_count, _ = qs.delete()
    return f"Удалено {deleted_count} записей"

@shared_task
def send_appointment_reminders():
    """
    Каждый день: отправляет письма о записях на завтра.
    """
    tomorrow = timezone.now().date() + timezone.timedelta(days=1)
    appointments = Appointment.objects.filter(date=tomorrow)
    for appt in appointments:
        # письмо клиенту
        send_mail(
            subject=f"Bellezza Salon: Напоминание о записи на {appt.date} в {appt.time}",
            message=(
                f"Здравствуйте {appt.client.name}!\n\n"
                f"Салон красоты Bellezza напоминает, что вы записаны на услугу:\n"
                f"• Услуга: {appt.service.name}\n"
                f"• Мастер: {appt.employee.name}\n"
                f"• Дата и время: {appt.date} в {appt.time}\n\n"
                f"Ждем вас в нашем салоне по адресу: [Москва, Большая Якиманка 26]\n"
                f"Телефон для связи: [+7 917 814 98 41 ]\n\n"
                f"С уважением,\n"
                f"Команда салона красоты Bellezza"
            ),
            from_email="Bellezza Salon <bellezza@example.com>",
            recipient_list=[appt.client.email],
            fail_silently=False,
        )
    return f"Отправлено напоминаний: {appointments.count()}"
