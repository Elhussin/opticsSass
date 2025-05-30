# settings.py
import os
from django.core.exceptions import ImproperlyConfigured

# إعداد قواعد البيانات المتعددة
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'main_db',
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# سيتم إضافة قواعد بيانات العملاء ديناميكياً
DATABASE_ROUTERS = ['core.routers.TenantDatabaseRouter']

# middleware.py - للتعرف على العميل الحالي
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # استخراج معرف العميل من الـ subdomain أو header
        host = request.get_host()
        tenant_id = self.extract_tenant_from_host(host)
        
        # حفظ معرف العميل في thread-local storage
        from django.db import connection
        connection.tenant = tenant_id
        
        response = self.get_response(request)
        return response
    
    def extract_tenant_from_host(self, host):
        """
        استخراج معرف العميل من الـ subdomain
        مثال: shop1.yourapp.com -> shop1
        """
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'www' and subdomain != 'api':
                return subdomain
        return None

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

# models.py - نماذج إدارة العملاء
from django.db import models
from django.contrib.auth.models import User

class Tenant(models.Model):
    """نموذج العميل الأساسي"""
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=50, unique=True)
    database_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # إعدادات العميل
    plan = models.CharField(max_length=20, choices=[
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ])
    max_users = models.IntegerField(default=5)
    max_products = models.IntegerField(default=1000)
    
    def __str__(self):
        return self.name

class TenantUser(models.Model):
    """ربط المستخدمين بالعملاء"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee')
    ])
    
    class Meta:
        unique_together = ('user', 'tenant')

# utils.py - أدوات إدارة العملاء
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.conf import settings
from django.core.management import execute_from_command_line

class TenantManager:
    @staticmethod
    def create_tenant_database(tenant_name):
        """إنشاء قاعدة بيانات جديدة للعميل"""
        db_name = f"tenant_{tenant_name}"
        
        # الاتصال بقاعدة البيانات الرئيسية لإنشاء قاعدة جديدة
        connection = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database='postgres'  # الاتصال بقاعدة postgres الافتراضية
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE {db_name}")
        cursor.close()
        connection.close()
        
        # إضافة قاعدة البيانات الجديدة للإعدادات
        settings.DATABASES[db_name] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': settings.DATABASES['default']['USER'],
            'PASSWORD': settings.DATABASES['default']['PASSWORD'],
            'HOST': settings.DATABASES['default']['HOST'],
            'PORT': settings.DATABASES['default']['PORT'],
        }
        
        return db_name
    
    @staticmethod
    def run_migrations_for_tenant(db_name):
        """تشغيل migrations على قاعدة بيانات العميل"""
        execute_from_command_line([
            'manage.py', 'migrate', 
            '--database', db_name,
            '--run-syncdb'
        ])

# views.py - إنشاء عميل جديد
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User

@api_view(['POST'])
def create_tenant(request):
    """إنشاء عميل جديد مع قاعدة بيانات منفصلة"""
    data = request.data
    
    try:
        # إنشاء قاعدة البيانات
        db_name = TenantManager.create_tenant_database(data['subdomain'])
        
        # إنشاء سجل العميل
        tenant = Tenant.objects.create(
            name=data['name'],
            subdomain=data['subdomain'],
            database_name=db_name,
            plan=data.get('plan', 'basic')
        )
        
        # تشغيل migrations على قاعدة البيانات الجديدة
        TenantManager.run_migrations_for_tenant(db_name)
        
        # إنشاء المستخدم المدير
        admin_user = User.objects.create_user(
            username=data['admin_email'],
            email=data['admin_email'],
            password=data['admin_password']
        )
        
        TenantUser.objects.create(
            user=admin_user,
            tenant=tenant,
            role='admin'
        )
        
        return Response({
            'success': True,
            'tenant_id': tenant.id,
            'subdomain': tenant.subdomain
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)