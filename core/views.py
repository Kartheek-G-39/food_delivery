from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout,get_user_model,update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from .models import Restaurant, Menu, MenuItem, CustomUser,Order,OrderItem,CartItem,Customer,Notification,DeliveryBoy
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, RestaurantRegistrationForm, CustomerRegistrationForm, DeliveryBoyRegistrationForm, LoginForm, MenuItemForm,ProfileForm,Order,OrderForm,CartItemForm,OrderItemFeedbackForm,OrderSearchForm
from django.http import JsonResponse
from rest_framework import serializers
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from .utils import create_notification
from django.contrib import messages
from django_ratelimit.decorators import ratelimit
import time
from urllib.parse import urlparse, parse_qs
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .exceptions import RateLimitExceeded


@login_required
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def profile(request):
    if getattr(request, 'limited', False):
        raise RateLimitExceeded()
    user = request.user
    user_specific_form = None

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=user)

        if hasattr(user, 'restaurant'):
            user_specific_form = RestaurantRegistrationForm(request.POST, instance=user.restaurant)
        elif hasattr(user, 'customer'):
            user_specific_form = CustomerRegistrationForm(request.POST, instance=user.customer)
        elif hasattr(user, 'delivery_boy'):
            user_specific_form = DeliveryBoyRegistrationForm(request.POST, instance=user.delivery_boy)

        if profile_form.is_valid():
            profile_form.save()

        if user_specific_form and user_specific_form.is_valid():
            user_specific_form.save()

        return redirect('profile')
    else:
        profile_form = ProfileForm(instance=user)

        if hasattr(user, 'restaurant'):
            user_specific_form = RestaurantRegistrationForm(instance=user.restaurant)
        elif hasattr(user, 'customer'):
            user_specific_form = CustomerRegistrationForm(instance=user.customer)
        elif hasattr(user, 'delivery_boy'):
            user_specific_form = DeliveryBoyRegistrationForm(instance=user.delivery_boy)

    context = {
        'profile_form': profile_form,
        'user_specific_form': user_specific_form,
        'password_form' : PasswordChangeForm(request.user),
        'user': user,
    }
    return render(request, 'core/profile.html', context)
@login_required
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def change_password(request):
    if getattr(request, 'limited', False):
        raise RateLimitExceeded()
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
    return render(request, 'core/profile.html', {
        'password_form': form
    })
@csrf_exempt
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user_type = request.POST.get('user_type')
            user.user_type = user_type
            user.save()
            if user_type == 'restaurant':
                restaurant_form = RestaurantRegistrationForm(request.POST,request.FILES)
                if restaurant_form.is_valid():
                    restaurant = restaurant_form.save(commit=False)
                    restaurant.user = user
                    restaurant.code = user.id
                    restaurant.save()
                    return redirect('login')
                else:
                    return render(request, 'core/register.html', {
                                            'error_form': user_form,
                                            'error_user_form': restaurant_form,
                                            'restaurant':True})
            elif user_type == 'customer':
                customer_form = CustomerRegistrationForm(request.POST)
                if customer_form.is_valid():
                    customer = customer_form.save(commit=False)
                    customer.user = user
                    customer.save()
                    return redirect('login')
                else:
                    return render(request, 'core/register.html', {
                                    'error_form': user_form,
                                    'error_user_form': customer_form,})
            elif user_type == 'delivery_boy':
                delivery_boy_form = DeliveryBoyRegistrationForm(request.POST)
                if delivery_boy_form.is_valid():
                    delivery_boy = delivery_boy_form.save(commit=False)
                    delivery_boy.user = user
                    delivery_boy.save()
                    return redirect('login')
                else:
                    return render(request, 'core/register.html', {
                                            'error_form': user_form,
                                            'error_user_form': restaurant_form,})
        user_type = request.POST.get('user_type')
        restaurant_form = RestaurantRegistrationForm(request.POST,request.FILES) if user_type == 'restaurant' else None
        customer_form = CustomerRegistrationForm(request.POST) if user_type == 'customer' else None
        delivery_boy_form = DeliveryBoyRegistrationForm(request.POST) if user_type == 'delivery_boy' else None
        return render(request, 'core/register.html', {
            'user_form': user_form,
            'restaurant_form': restaurant_form,
            'customer_form': customer_form,
            'delivery_boy_form': delivery_boy_form,
            'error_form': user_form,  # Display errors for user_form by default
            'error_user_form': restaurant_form if user_type == 'restaurant' else
                              customer_form if user_type == 'customer' else
                              delivery_boy_form if user_type == 'delivery_boy' else None,
            'restaurant':True if user_type == 'restaurant' else False,
        })
    else:
        user_form = CustomUserCreationForm()
        restaurant_form = RestaurantRegistrationForm()
        customer_form = CustomerRegistrationForm()
        delivery_boy_form = DeliveryBoyRegistrationForm()
        return render(request, 'core/register.html', {
            'user_form': user_form,
            'restaurant_form': restaurant_form,
            'customer_form': customer_form,
            'delivery_boy_form': delivery_boy_form
        })

@login_required
def get_restaurants_by_city(request, city):

    page = request.GET.get('page', 1)  # Get the current page number from the request
    per_page = 10  # Number of items per page

    restaurants = Restaurant.objects.filter(city=city).order_by('name')
    paginator = Paginator(restaurants, per_page)

    try:
        restaurants_page = paginator.page(page)
    except PageNotAnInteger:
        restaurants_page = paginator.page(1)
    except EmptyPage:
        restaurants_page = paginator.page(paginator.num_pages)

    data = []
    for restaurant in restaurants_page:
        restaurant_name = restaurant.name.strip('#')
        restaurant_data = {
            'name': restaurant.name,
            'user': restaurant.user.id,
            'address': restaurant.address,
            'min_item_price': restaurant.get_min_item_price(),
            'max_item_price': restaurant.get_max_item_price(),
            'total_orders': restaurant.get_total_orders(),
        }
        data.append(restaurant_data)

    response_data = {
        'restaurants': data,
        'has_next': restaurants_page.has_next(),
        'has_previous': restaurants_page.has_previous(),
        'num_pages': paginator.num_pages,
        'current_page': restaurants_page.number,
    }

    return JsonResponse(response_data)

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'

@csrf_protect
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def user_login(request):
    if getattr(request, 'limited', False):
        raise RateLimitExceeded()
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                # Handle invalid credentials with user-friendly messages
                context = {'form': form, 'error_message': 'Invalid username or password.'}
                return render(request, 'core/login.html', context)
        else:
            print(form.errors)
            return render(request, 'core/login.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def home(request):
    user = request.user
    if user.user_type == 'customer':
        cities = Restaurant.objects.values_list('city', flat=True).distinct()
        unread_notifications = user.notifications.filter(read=False).values('message','id')
        context={'cities': cities,'unread_notifications':unread_notifications}
        return render(request, 'core/customer_home.html', context)
    elif user.user_type == 'restaurant':
        current_orders = Order.objects.filter(
        restaurant=request.user.restaurant,
        status__in=['Ordered','Accepted by Restaurant','Ready for Pickup','Accepted by Delivery Boy','Picked Up','Reached Location']
        ).order_by('-id')
        last_five_notifications = Notification.objects.filter(
            user=request.user,
            notification_type = "new_order",
        ).order_by('-timestamp')[:5]
        past_orders= Order.objects.filter(restaurant = request.user.restaurant,status = 'Delivered').order_by('-id')    
        paginator = Paginator(past_orders, 5)  # Show 5 past orders per page.
        page_number = request.GET.get('page')
        past_orders = paginator.get_page(page_number)
        unread_notifications = user.notifications.filter(read=False).values('message','id')
        context = {
            'current_orders': current_orders,
            'last_five_notifications': last_five_notifications,
            'past_orders': past_orders,
            'unread_notifications':unread_notifications,
        }
        return render(request, 'core/restaurant_home.html',context  )
    elif user.user_type == 'delivery_boy':
        order = Order.objects.filter(delivery_boy=user.delivery_boy).exclude(status='Delivered').order_by('-id').first()
        
        # If there's no open order, get the 5 most recent delivered orders
        recent_orders = Order.objects.filter(delivery_boy=user.delivery_boy, status='Delivered').order_by('-order_time')[:5]
        unread_notifications = user.notifications.filter(read=False).values('message','id')
        context = {
            'delivery_boy_status': user.delivery_boy.status,
            'order': order,
            'recent_orders': recent_orders,
            'unread_notifications':unread_notifications,
        }
        return render(request, 'core/delivery_boy_home.html',context)
    return redirect('login')

@login_required
def restaurant_management(request):
    try:
        restaurant = Restaurant.objects.get(user=request.user)
        menu = Menu.objects.get(restaurant=restaurant)
    except Menu.DoesNotExist:
        menu = Menu.objects.create(restaurant=restaurant, name=f"{restaurant.name}'s Menu")

    if request.method == 'POST':
        form = MenuItemForm(request.POST)
        if form.is_valid():
            # Save the menu item with the associated menu
            menu_item = form.save(commit=False)
            menu_item.menu = menu
            menu_item.save()
            return redirect('restaurant_management')
    else:
        form = MenuItemForm(restaurant=restaurant)

    return render(request, 'core/restaurant_management.html', {'form': form, 'menu': menu})

@login_required
def cities(request):
    cities = Restaurant.objects.values_list('city', flat=True).distinct()
    return render(request, 'core/cities.html', {'cities': cities})

@login_required
def menu_items(request, restaurant):
    user = CustomUser.objects.get(id=restaurant)
    restaurant_instance = Restaurant.objects.get(user=user)
    menu_items = MenuItem.objects.filter(menu__restaurant=restaurant_instance)
    context={
        'menu_items' : menu_items,
        'restaurant' : restaurant_instance,
        'customer' : user
    }
    return render(request, 'core/menu_items.html', context)

@login_required
def add_to_cart(request, menu_item_id):
    menu_item = MenuItem.objects.get(id=menu_item_id)
    customer = request.user.customer
    cart_item, created = CartItem.objects.get_or_create(customer=customer, menu_item=menu_item)

    if request.method == 'POST':
        form = CartItemForm(request.POST, instance=cart_item)
        if form.is_valid():
            form.save()
            return redirect('cart')

    form = CartItemForm(instance=cart_item)
    return render(request, 'core/add_to_cart.html', {'form': form, 'menu_item': menu_item})

@login_required
def cart(request):
    customer = request.user.customer
    cart_items = CartItem.objects.filter(customer=customer)
    return render(request, 'core/cart.html', {'cart_items': cart_items})


@login_required
def order_success(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'core/order_success.html', {'order': order})

User = get_user_model()


def place_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        items = data.get('items', [])
        location_link = data.get('location_link')
        preorder_date = data.get('preorderDate',None)
        address = data.get('delivery_address',None)
        number = data.get('phone_number')
        price=data.get('price')
        restaurant_id=int(data.get('restaurant_id'))
        restaurant=Restaurant.objects.get(id=restaurant_id)
        customer=Customer.objects.get(user=request.user)
        print(restaurant,customer)
        order = Order.objects.create(customer = customer,delivery_address=address,location = location_link,restaurant=restaurant, scheduled_time=preorder_date,total_price=price,contact = number)
        for item in items:
            menu_item = MenuItem.objects.get(id=item['id'])
            OrderItem.objects.create(order=order, menu_item=menu_item, quantity=item['quantity'],price=price)
        restaurant_message = f"You have received a new order #{order.id}."
        create_notification(order.restaurant.user, restaurant_message,notification_type="new_order")
        return JsonResponse({'message': 'Order placed successfully!','order_id':order.id})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def view_orders(request):
    orders=[]
    if request.user.user_type == 'restaurant':
        orders = Order.objects.filter(restaurant=request.user.restaurant).order_by('-order_time')
    elif request.user.user_type == 'customer':
        orders = Order.objects.filter(customer=request.user.customer).order_by('-order_time')
    else:
        orders = Order.objects.filter(delivery_boy = request.user.delivery_boy).order_by('-order_time')
    
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        orders = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        orders = paginator.page(paginator.num_pages)
    return render(request, 'core/view_orders.html', {'orders': orders})



def dummy_payment_page(request,order_id):
    context = {
        'total_amount': 1000,
        'order_id' : order_id,
    }
    return render(request, 'core/dummy_payment.html', context)

@csrf_exempt
def dummy_verify_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        order = get_object_or_404(Order,id=order_id)
        order.update_payment_status("SuccessFull")
        return JsonResponse({'status': 'Payment successful'})
    return JsonResponse({'status': 'Invalid request method'}, status=400)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer)
    if request.method == 'POST':
        form = OrderItemFeedbackForm(request.POST)
        if form.is_valid():
            feedback_text = request.POST.get('feedbackText')
            feedback_rating = request.POST.get('feedbackRating')
            item_id = request.POST.get('orderitemid')
            order_item = get_object_or_404(OrderItem, id=item_id)
            order_item.rating = feedback_rating
            order_item.feedback = feedback_text
            order_item.save()
            restaurant_message = f"Feedback received for item {order_item.menu_item.item} in order #{order_item.order.id}."
            create_notification(order_item.order.restaurant.user, restaurant_message)
            return redirect('orders')
    else:
        form = OrderItemFeedbackForm()
    return render(request, 'order_detail.html', {'order': order, 'form': form})

def notifications_list(request):
    notifications = request.user.notifications.all().order_by('-timestamp')
    return render(request, 'core/notifications_list.html', {'notifications': notifications})

def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return redirect('notifications')

def notify_free_delivery_boys(message,order):
    while True:
        free_delivery_boys = DeliveryBoy.objects.filter(status='online', free=True)
        if free_delivery_boys.exists():
            for delivery_boy in free_delivery_boys:
                create_notification(delivery_boy.user, message,order=order,notification_type="order")
            break  # Exit the loop once notifications are sent to available delivery boys
        else:
            # If no free delivery boys are available, wait for some time before checking again
            time.sleep(10) 

def assign_delivery_boy(request, order_id, delivery_boy_id):
    order = get_object_or_404(Order, id=order_id)
    delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id)
    order.delivery_boy = delivery_boy
    order.change_status('Accepted by Delivery Boy')
    order.save()
    return redirect('orders')

@login_required
def change_order_status(request, order_id, new_status):
    order = get_object_or_404(Order, id=order_id)
    user = request.user
    allowed_transitions = {
        'Accepted by Restaurant': ['Accepted by Delivery Boy'],
        'Accepted by Delivery Boy': ['Ready for Pickup'],
        'Ready for Pickup': ['Picked Up'],
        'Picked Up': ['Reached Location'],
        'Reached Location': ['Delivered']
    }
    if user.user_type == 'restaurant' and new_status in ['Accepted by Restaurant', 'Ready for Pickup']:
        order.status = new_status
        order.save()
        create_notification(order.customer.user, f"Your order #{order.id} status has been updated to {new_status}.", order=order, notification_type='Order Status')
        if new_status == 'Accepted by Restaurant':
            create_notification(order.customer.user, f"Your order #{order.id} status has been updated to {new_status}.", order=order, notification_type='Order Status')
            notify_free_delivery_boys(f"Order #{order.id} is available to deliver from {order.restaurant.name}.",order)
    elif user.user_type == 'delivery_boy' and new_status in ['Accepted by Delivery Boy','Reached Location',  'Picked Up', 'Delivered']:
        if new_status in allowed_transitions.get(order.status, []):
            order.status = new_status
            order.save()
            create_notification(order.customer.user, f"Your order #{order.id} status has been updated to {new_status}.")
            if new_status == 'Accepted by Delivery Boy':
                if not order.delivery_boy:
                    order.delivery_boy = user.delivery_boy
                    order.delivery_boy.free = False
                    order.save()
                    create_notification(order.customer.user, f"Your order #{order.id} status has been updated to {new_status}.", order=order, notification_type='Order Status')
                    create_notification(order.restaurant.user, f"Delivery boy has accepted order #{order.id}.", order=order, notification_type='Order Status')
                else:
                    messages.warning(request, f"Order #{order.id} already has a delivery boy assigned.")
            elif new_status == 'Picked Up':
                create_notification(order.customer.user, f"Your order #{order.id} has been picked up by the delivery boy.")
            elif new_status == 'Delivered':
                create_notification(order.customer.user, f"Your order #{order.id} has been delivered.")
                order.delivery_boy.free=True
        else:
            messages.warning(request, f"Order #{order.id} cannot be marked as {new_status} from its current status.")
    if user.user_type == "customer":
        return redirect('orders')
    else:
        return redirect('home')



@login_required
def change_delivery_boy_status(request, status):
    if request.user.user_type == 'delivery_boy':
        delivery_boy = request.user.delivery_boy
        order = Order.objects.filter(delivery_boy=delivery_boy).exclude(status__in=['Delivered','Undelivered']).order_by('-id').first()
        if order:
            return JsonResponse({'success': False,'message':'Complete the pending order to go Offline'})
        if status in ['online', 'offline']:
            try:
                request.user.delivery_boy.status = status
                request.user.delivery_boy.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)


def update_delivery_boy_location(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        lat = data['lat']
        lng = data['lng']
        order_id = data['order_id']  # Get the order ID from the request

        # Broadcast the location to the WebSocket group specific to the order
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'order_{order_id}',  # Send to a group named after the order ID
            {
                'type': 'status_update',
                'message': json.dumps({'lat': lat, 'lng': lng})
            }
        )
        
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    

def room(request, room_name):
    return render(request, "chat/room.html", {"room_name": room_name})

@login_required  # Ensures the user is authenticated
 # Ensures only POST requests are allowed
def mark_all_as_read(request):
    try:
        # Mark all notifications as read for the current user
        notifications = Notification.objects.filter(user=request.user, read=False)
        notifications.update(read=True)

        # Optionally, you can return a success message or status
        return JsonResponse({'message': 'All notifications marked as read successfully'}, status=200)
    
    except Exception as e:
        # Handle exceptions or errors
        return JsonResponse({'error': str(e)}, status=500)
    
