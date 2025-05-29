import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'optica_saas.settings')
django.setup()

from core.models import Tenant
from django.db import connections
from django.core.management import call_command

def create_tenant(name, subdomain):
    db_name = f"{subdomain}_db"

    tenant = Tenant.objects.create(
        name=name,
        subdomain=subdomain,
        db_name=db_name
    )

    with connections['default'].cursor() as cursor:
        cursor.execute(f"CREATE DATABASE {db_name};")

    call_command('migrate', database=db_name)
    print(f"[✔] Tenant '{name}' created with DB: {db_name}")

# مثال:
# create_tenant("Vision Store", "vision")
