# routers/db_router.py
# routers.py
class TenantRouter:
    def db_for_read(self, model, **hints):
        request = hints.get('request')
        return getattr(request, 'tenant_db', None) or 'default'

    def db_for_write(self, model, **hints):
        request = hints.get('request')
        return getattr(request, 'tenant_db', None) or 'default'
