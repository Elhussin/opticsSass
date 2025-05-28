# routers/db_router.py
# routers.py
# class TenantRouter:
#     def db_for_read(self, model, **hints):
#         request = hints.get('request')
#         return getattr(request, 'tenant_db', None) or 'default'

#     def db_for_write(self, model, **hints):
#         request = hints.get('request')
#         return getattr(request, 'tenant_db', None) or 'default'
# routers.py - توجيه الاستعلامات لقاعدة البيانات المناسبة
from django.conf import settings
from threading import local

_thread_locals = local()

class TenantDatabaseRouter:
    def db_for_read(self, model, **hints):
        """تحديد قاعدة البيانات للقراءة"""
        if hasattr(_thread_locals, 'tenant_id') and _thread_locals.tenant_id:
            db_name = f"tenant_{_thread_locals.tenant_id}"
            if db_name in settings.DATABASES:
                return db_name
        return 'default'

    def db_for_write(self, model, **hints):
        """تحديد قاعدة البيانات للكتابة"""
        if hasattr(_thread_locals, 'tenant_id') and _thread_locals.tenant_id:
            db_name = f"tenant_{_thread_locals.tenant_id}"
            if db_name in settings.DATABASES:
                return db_name
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """السماح بالـ migrations على قواعد البيانات المناسبة"""
        if db == 'default':
            # قاعدة البيانات الرئيسية للمعلومات المشتركة
            return app_label in ['tenants', 'auth', 'contenttypes', 'sessions']
        else:
            # قواعد بيانات العملاء للنماذج الخاصة بهم
            return app_label in ['glasses_store', 'inventory', 'sales']