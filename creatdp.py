from django.core.management import call_command
from django.db import connections
import psycopg2

def create_new_client_db(db_name, db_user, db_password):
    # إنشاء قاعدة بيانات (PostgreSQL مثال)
    conn = psycopg2.connect(dbname='postgres', user='postgres', password='yourpass')
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE {db_name};")
    cursor.close()
    conn.close()

    # إعداد الاتصال مؤقتًا
    settings.DATABASES[db_name] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': 'localhost',
        'PORT': '',
    }

    # تنفيذ المايجريشن
    call_command('migrate', database=db_name)
