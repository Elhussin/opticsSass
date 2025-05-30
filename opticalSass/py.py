from pathlib import Path
import shutil
import zipfile

# إنشاء هيكل مشروع Django starter (مبسط)
project_root = Path("/mnt/data/optica_saas_starter")
core_dir = project_root / "core"
tenant_dir = project_root / "tenant"
middleware_dir = project_root / "middleware"
routers_dir = project_root / "routers"
scripts_dir = project_root / "scripts"
main_project_dir = project_root / "optica_saas"

# إنشاء المجلدات
for folder in [core_dir, tenant_dir, middleware_dir, routers_dir, scripts_dir, main_project_dir]:
    folder.mkdir(parents=True, exist_ok=True)

# ملفات core/models.py
(core_dir / "models.py").write_text("""\
from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=100, unique=True)
    db_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
""")

# ملفات tenant/models.py
(tenant_dir / "models.py").write_text("""\
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('sales', 'Sales'),
        ('tech', 'Technician'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
""")

# middleware/tenant_middleware.py
(middleware_dir / "tenant_middleware.py").write_text("""\
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
            request.tenant_db = None

        return self.get_response(request)
""")

# routers/db_router.py
(routers_dir / "db_router.py").write_text("""\
class TenantRouter:
    def db_for_read(self, model, **hints):
        request = hints.get('request')
        return getattr(request, 'tenant_db', None) or 'default'

    def db_for_write(self, model, **hints):
        request = hints.get('request')
        return getattr(request, 'tenant_db', None) or 'default'
""")

# scripts/create_tenant.py
(scripts_dir / "create_tenant.py").write_text("""\
import psycopg2
from django.core.management import call_command
from django.conf import settings

def create_tenant_db(db_name, db_user, db_password):
    conn = psycopg2.connect(dbname='postgres', user=db_user, password=db_password)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE {db_name};")
    cursor.close()
    conn.close()

    settings.DATABASES[db_name] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': 'localhost',
        'PORT': '',
    }

    call_command('migrate', database=db_name)
""")

# إعداد ملف settings.py بسيط
(main_project_dir / "settings.py").write_text("""\
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'core_db',
        'USER': 'youruser',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '',
    }
}

DATABASE_ROUTERS = ['routers.db_router.TenantRouter']

AUTH_USER_MODEL = 'tenant.CustomUser'
MIDDLEWARE = [
    'middleware.tenant_middleware.TenantMiddleware',
]
""")

# إنشاء ملف zip
zip_path = "/mnt/data/optica_saas_starter.zip"
shutil.make_archive(zip_path.replace(".zip", ""), 'zip', project_root)

zip_path
