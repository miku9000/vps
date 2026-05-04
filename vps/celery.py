import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vps.settings")

app = Celery("vps")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()