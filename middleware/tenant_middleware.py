# middleware.py
from core.models import Tenant

# class TenantMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         host = request.get_host().split(':')[0]  # remove port if exists
#         subdomain = host.split('.')[0]

#         try:
#             tenant = Tenant.objects.get(subdomain=subdomain)
#             request.tenant_db = tenant.db_name
#         except Tenant.DoesNotExist:
#             request.tenant_db = None

#         return self.get_response(request)
# class TenantMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # استخراج معرف العميل من الـ subdomain أو header
#         host = request.get_host()
#         tenant_id = self.extract_tenant_from_host(host)
        
#         # حفظ معرف العميل في thread-local storage
#         from django.db import connection
#         connection.tenant = tenant_id
        
#         response = self.get_response(request)
#         return response
    
#     def extract_tenant_from_host(self, host):
#         """
#         استخراج معرف العميل من الـ subdomain
#         مثال: shop1.yourapp.com -> shop1
#         """
#         if '.' in host:
#             subdomain = host.split('.')[0]
#             if subdomain != 'www' and subdomain != 'api':
#                 return subdomain
#         return None

from core.models import Tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        subdomain = host.split('.')[0]

        try:
            tenant = Tenant.objects.get(subdomain=subdomain)
            request.tenant_db = tenant.db_name
        except Tenant.DoesNotExist:
            request.tenant_db = 'default'

        return self.get_response(request)
