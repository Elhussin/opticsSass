from django.shortcuts import render

# Create your views here.
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