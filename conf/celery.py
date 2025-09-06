import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")

app = Celery("conf")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


# Тестовая debug-задача
@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Расписание
app.conf.beat_schedule = {
    "send-appointment-reminders-every-day-8am": {
        "task": "beauty_salon.tasks.send_appointment_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    "delete-old-appointments-monthly": {
        "task": "beauty_salon.tasks.delete_old_appointments",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),
    },
}
