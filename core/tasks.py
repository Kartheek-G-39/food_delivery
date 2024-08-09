# core/tasks.py

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import timedelta
from django.utils import timezone
from .models import Order

logger = get_task_logger(__name__)

@shared_task
def update_orders_task():
    logger.info("Updating orders task started")

    # Define default arguments (e.g., two_hours_ago)
    two_hours_ago = timezone.now() - timedelta(hours=2)

    # Example task logic: Update orders that are not delivered and not updated within 2 hours
    orders_to_update = Order.objects.filter(
        status='Undelivered',
        updated_at__lte=two_hours_ago
    )

    for order in orders_to_update:
        # Update order status or perform other actions
        order.status = 'Pending'
        order.save()

    logger.info("Updating orders task completed")
