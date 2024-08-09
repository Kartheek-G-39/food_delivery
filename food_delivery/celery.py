# food_delivery/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_delivery.settings')

app = Celery('food_delivery')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configure periodic tasks using Celery Beat
from celery.schedules import crontab

app.conf.beat_schedule = {
    'update_orders_every_two_hours': {
        'task': 'core.tasks.update_orders_task',  # Specify the task name
        'schedule': crontab(minute=0, hour='*/2'),  # Executes every 2 hours
        # You can add other options here as needed
    },
}

# Optionally configure timezone
app.conf.timezone = 'Asia/Kolkata'

# Optionally configure Celery result backend
app.conf.result_backend = 'redis://127.0.0.1:6379/1'

if __name__ == '__main__':
    app.start()
