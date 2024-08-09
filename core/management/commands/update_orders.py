# orders/management/commands/update_orders.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Order  # Replace with your actual Order model

class Command(BaseCommand):
    help = 'Update orders to undelivered status after 2 hours of delivery'
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("hi"))
        # Calculate the datetime 2 hours ago
        two_hours_ago = timezone.now() - timezone.timedelta(hours=2)

        # Query for orders delivered more than 2 hours ago
        orders_to_update = Order.objects.exclude(
            status__in=['Delivered', 'Undelivered']
        ).filter(
            order_time__lte=two_hours_ago
        )

        # Update status to 'Undelivered'
        orders_to_update.update(status='Undelivered')

        self.stdout.write(self.style.SUCCESS('Orders updated successfully'))

