from django.urls import path,re_path,include
from django.views.generic.base import RedirectView
from . import views
from . import consumers

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('accounts/login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('', views.home, name='home'),
    path('cities/', views.cities, name='cities'),
    path('profile/', views.profile, name='profile'),
    path('menu_items/<str:restaurant>/', views.menu_items, name='menu_items'),
    path('restaurant_management/', views.restaurant_management, name='restaurant_management'),
    path('api/restaurants/<str:city>/', views.get_restaurants_by_city, name='get_restaurants_by_city'),
    path('add_to_cart/<int:menu_item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('api/place_order/', views.place_order, name='place_order'),
    path('order_success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.view_orders, name='orders'),
    path('dummy-payment/<int:order_id>/', views.dummy_payment_page, name='dummy_payment_page'),
    path('dummy-verify-payment/', views.dummy_verify_payment, name='dummy_verify_payment'),
    path('order_detail/<int:order_id>/',views.order_detail,name='order_detail'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('orders/status/<int:order_id>/<str:new_status>/', views.change_order_status, name='change_order_status'),
    path('change-status/<str:status>/', views.change_delivery_boy_status, name='change_delivery_boy_status'),
    path('update_delivery_boy_location/', views.update_delivery_boy_location, name='update_delivery_boy_location'),
    path('<int:order_id>/',views.room,name = 'room'),
    path('mark_all_as_read/', views.mark_all_as_read, name='mark_all_as_read'),
    path("__reload__/", include("django_browser_reload.urls")),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico'), name='favicon'),
    path('change_password/', views.change_password, name='change_password'),

]
