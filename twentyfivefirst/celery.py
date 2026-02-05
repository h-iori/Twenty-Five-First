import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "twentyfivefirst.settings")
import django
django.setup()

app = Celery("twentyfivefirst")


# Load config from Django settings, the CELERY_ namespace will be used
app.config_from_object("django.conf:settings", namespace="CELERY")


# Auto-discover tasks from installed apps
app.autodiscover_tasks()
import mainapp.tasks.email
import mainapp.tasks.cart


# sensible defaults for reliability
app.conf.update(
task_acks_late=True,
worker_prefetch_multiplier=1,
task_default_queue="default",
task_routes={
"mainapp.tasks.email.send_email_task": {"queue": "emails"},
},
worker_max_tasks_per_child=200,
)


