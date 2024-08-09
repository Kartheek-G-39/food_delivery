# exceptions.py
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

class RateLimitExceeded(PermissionDenied):
    pass

def custom_exception_handler(get_response):
    def middleware(request):
        response = get_response(request)
        if isinstance(response, RateLimitExceeded):
            return JsonResponse({"error": "Rate limit exceeded. Please try again later."}, status=429)
        return response
    return middleware
