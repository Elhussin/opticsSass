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