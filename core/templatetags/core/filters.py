from django import template
from ...models import Restaurant
register = template.Library()

@register.filter
def get_total_orders(restaurant):
    try:
        return restaurant.user.orders.count()
    except Restaurant.DoesNotExist:
        return 0  # Or return a different default value
    except AttributeError:
        return 0
@register.filter
def unread_count(queryset):
  return queryset.filter(read=False).count()

@register.filter
def undelivered_count(queryset):
  if queryset:
    return queryset.exclude(status__iexact="Delivered").count()
  else:
    return 0

