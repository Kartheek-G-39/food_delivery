from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('restaurant', 'Restaurant'),
        ('delivery_boy', 'Delivery Boy'),
    )
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES)

class Restaurant(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,related_name='restaurant')
    name = models.CharField(max_length=255)
    code=models.CharField(max_length=10)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15,null=True)
    city = models.CharField(max_length=100)
    cuisine = models.CharField(max_length=100)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    image = models.ImageField(upload_to='media/restaurant_images/',null=True)

    def get_total_orders(self):
        try:
            return self.orders.count()
        except:
            return 0

    def get_min_item_price(self):
        try:
            return MenuItem.objects.filter(menu__restaurant=self).order_by('price').first().price
        except:
            return 0

    def get_max_item_price(self):
        try:
            return MenuItem.objects.filter(menu__restaurant=self).order_by('-price').first().price
        except:
            return 0

    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,related_name="customer")
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)

class DeliveryBoy(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,related_name='delivery_boy')
    phone_number = models.CharField(max_length=15)
    vehicle_number = models.CharField(max_length=15)
    status = models.CharField(max_length=10, choices=(('Online', 'Online'), ('Offline', 'Offline')), default='Offline')
    free = models.BooleanField(default=True)

    def change_status(self, status):
        self.status = status
        self.save()

class Menu(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menus')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
class MenuItem(models.Model):
    VEG = 'Veg'
    NON_VEG = 'Non-Veg'
    VEG_OR_NON_VEG_CHOICES = [
        (VEG, 'Veg'),
        (NON_VEG, 'Non-veg'),
    ]

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='menu_items')
    item = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    veg_or_non_veg = models.CharField(max_length=10, choices=VEG_OR_NON_VEG_CHOICES)

    def __str__(self):
        return f"{self.item} ({self.menu.restaurant.name})"


class CartItem(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cart_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    STATUS_CHOICES = [
        ('Ordered', 'Ordered'),
        ('Accepted by Restaurant', 'Accepted by Restaurant'),
        ('Ready for Pickup', 'Ready for Pickup'),
        ('Accepted by Delivery Boy', 'Accepted by Delivery Boy'),
        ('Picked Up', 'Picked Up'),
        ('Delivered', 'Delivered'),
        ('Undelivered','Undelivered'),
        ('Reached Location','Reached Location')
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    delivery_boy = models.ForeignKey(DeliveryBoy, on_delete=models.DO_NOTHING, related_name='orders', null=True, blank=True)
    delivery_address = models.CharField(max_length=255, null=True)
    location = models.URLField(null=False, blank=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_time = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Ordered')
    contact = models.CharField(max_length=20, default='')
    payment = models.CharField(max_length=255, null=True, default="Pending")

    def update_payment_status(self, status):
        self.payment = status
        self.save()

    def default_contact(self):
        return self.customer.phone_number

    def save(self, *args, **kwargs):
        if not self.contact:
            self.contact = self.default_contact()
        super().save(*args, **kwargs)

    def change_status(self, new_status):
        self.status = new_status
        self.save()
        OrderStatusHistory.objects.create(order=self, status=new_status)
        self.notify_users(new_status)
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    def get_feedback_form(self):
        from .forms import OrderItemFeedbackForm
        form = OrderItemFeedbackForm(initial={'order_item_id': self.id})
        return form
    

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    order = models.ForeignKey('Order', null=True, blank=True, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:20]}..."
    
class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.status} at {self.timestamp}"