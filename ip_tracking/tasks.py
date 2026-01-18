from celery import shared_task
from django.utils import timezone
from django.db.models import Count
from ip_tracking.models import RequestLog, SuspiciousIP

SENSITIVE_PATHS = ['/admin', '/login']

@shared_task
def detect_anomalies():
    now = timezone.now()
    one_hour_ago = now - timezone.timedelta(hours=1)
    # Flag IPs with >100 requests/hour
    ip_counts = (
        RequestLog.objects
        .filter(timestamp__gte=one_hour_ago)
        .values('ip_address')
        .annotate(request_count=Count('id'))
        .filter(request_count__gt=100)
    )
    for entry in ip_counts:
        SuspiciousIP.objects.get_or_create(
            ip_address=entry['ip_address'],
            reason='>100 requests/hour'
        )
    # Flag IPs accessing sensitive paths
    for path in SENSITIVE_PATHS:
        logs = RequestLog.objects.filter(timestamp__gte=one_hour_ago, path__startswith=path)
        for log in logs:
            SuspiciousIP.objects.get_or_create(
                ip_address=log.ip_address,
                reason=f'Accessed sensitive path: {path}'
            )
