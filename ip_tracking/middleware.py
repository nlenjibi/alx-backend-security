from django.http import HttpResponseForbidden
from .models import RequestLog, BlockedIP


class IPLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.utils import timezone
        # Get IP address
        ip = self.get_client_ip(request)
        # Block request if IP is blacklisted
        from .models import BlockedIP
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("IP blocked")

        # Geolocation lookup with caching
        from django.core.cache import cache
        country, city = None, None
        cache_key = f'geo_{ip}'
        geo = cache.get(cache_key)
        if geo:
            country, city = geo.get('country'), geo.get('city')
        else:
            try:
                from ipgeolocation import IpGeolocationAPI
                api = IpGeolocationAPI()
                geo_data = api.get_geolocation(ip_address=ip)
                country = geo_data.get('country_name')
                city = geo_data.get('city')
                cache.set(cache_key, {'country': country, 'city': city}, 60 * 60 * 24)  # 24 hours
            except Exception:
                country, city = None, None

        # Log the request with geolocation
        RequestLog.objects.create(
            ip_address=ip,
            timestamp=timezone.now(),
            path=request.path,
            country=country,
            city=city
        )
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip