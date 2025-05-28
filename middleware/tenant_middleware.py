# middleware.py
from core.models import Tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # remove port if exists
        subdomain = host.split('.')[0]

        try:
            tenant = Tenant.objects.get(subdomain=subdomain)
            request.tenant_db = tenant.db_name
        except Tenant.DoesNotExist:
            request.tenant_db = None

        return self.get_response(request)
