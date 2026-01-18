from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from ratelimit.decorators import ratelimit

# Example sensitive view: login
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def login_view(request):
    if request.method == 'POST':
        # Dummy login logic for demonstration
        return HttpResponse('Login attempt')
    return HttpResponse('Login page')

# Example for anonymous users (stricter limit)
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def anonymous_sensitive_view(request):
    return HttpResponse('Sensitive action for anonymous users')
