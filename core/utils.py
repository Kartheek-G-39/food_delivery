# utils.py
from .models import Notification

def create_notification(user, message, order=None, notification_type=None):
    Notification.objects.create(user=user, message=message, order=order, notification_type=notification_type)

def delete_related_notifications(order, notification_type):
    Notification.objects.filter(order=order, notification_type=notification_type).delete()

