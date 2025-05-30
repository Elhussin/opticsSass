# الاستراتيجية الأولى: Single Database Multi-Tenant (الأكثر شيوعاً)
# ======================================================================

# models.py - النموذج الأساسي مع TenantMixin
from django.db import models
import uuid

class TenantMixin(models.Model):
    """
    Mixin يضيف tenant_id لكل نموذج
    هذا النهج يستخدم قاعدة بيانات واحدة مع فصل البيانات بـ tenant_id
    """
    tenant = models.ForeignKey(
        'tenants.Tenant', 
        on_delete=models.CASCADE,
        db_index=True,  # فهرسة لتحسين الأداء
        editable=False  # لا يمكن تعديله من الواجهة
    )
    
    class Meta:
        abstract = True

class Tenant(models.Model):
    """نموذج العميل المحسّن"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=50, unique=True, db_index=True)
    
    # إعدادات الخطة والحدود
    plan = models.CharField(max_length=20, choices=[
        ('free', 'مجاني'),
        ('basic', 'أساسي'),
        ('premium', 'متميز'),
        ('enterprise', 'مؤسسي')
    ])
    
    # حدود الاستخدام (Feature Flags)
    max_users = models.IntegerField(default=5)
    max_products = models.IntegerField(default=1000)
    max_storage_mb = models.IntegerField(default=100)
    
    # الميزات المتاحة
    features = models.JSONField(default=dict, help_text="""
    مثال: {
        'advanced_analytics': True,
        'api_access': False,
        'custom_branding': True,
        'multi_location': False
    }
    """)
    
    # معلومات الدفع والفوترة
    billing_email = models.EmailField()
    subscription_status = models.CharField(max_length=20, choices=[
        ('trial', 'تجريبي'),
        ('active', 'نشط'),
        ('past_due', 'متأخر الدفع'),
        ('cancelled', 'ملغي'),
        ('suspended', 'معلق')
    ], default='trial')
    
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    subscription_ends_at = models.DateTimeField(null=True, blank=True)
    
    # الحالة والتواريخ
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def has_feature(self, feature_name):
        """فحص إذا كان العميل يملك ميزة معينة"""
        return self.features.get(feature_name, False)
    
    def is_within_limits(self, resource_type):
        """فحص إذا كان العميل ضمن حدود الاستخدام"""
        if resource_type == 'users':
            current_users = self.users.filter(is_active=True).count()
            return current_users < self.max_users
        elif resource_type == 'products':
            current_products = self.products.filter(is_active=True).count()
            return current_products < self.max_products
        return True

# نماذج التطبيق مع TenantMixin
class Product(TenantMixin):
    """منتج مع دعم Multi-Tenant"""
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # ضمان فرادة SKU داخل كل tenant
        unique_together = [['tenant', 'sku']]
        # فهارس محسّنة للاستعلامات الشائعة
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['tenant', 'brand']),
            models.Index(fields=['tenant', 'created_at']),
        ]

class Brand(TenantMixin):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [['tenant', 'name']]

# middleware.py - Middleware محسّن للتعامل مع المستأجرين
from django.http import Http404
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware:
    """
    Middleware محسّن يتعامل مع:
    1. استخراج معرف العميل من الـ subdomain
    2. التحقق من صحة العميل وحالته
    3. حفظ معلومات العميل في thread-local storage
    4. التعامل مع الـ caching
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # استخراج العميل من الطلب
        tenant = self.get_tenant_from_request(request)
        
        if tenant is None and not self.is_excluded_path(request.path):
            raise Http404("العميل غير موجود")
        
        # حفظ العميل في الطلب
        request.tenant = tenant
        
        # تفعيل السياق للعميل الحالي
        if tenant:
            self.activate_tenant(tenant)
        
        response = self.get_response(request)
        
        # تنظيف السياق
        self.deactivate_tenant()
        
        return response
    
    def get_tenant_from_request(self, request):
        """استخراج العميل من الطلب مع الـ caching"""
        host = request.get_host().lower()
        
        # استخراج الـ subdomain
        subdomain = self.extract_subdomain(host)
        if not subdomain:
            return None
        
        # محاولة الحصول على العميل من الـ cache أولاً
        cache_key = f"tenant:{subdomain}"
        tenant = cache.get(cache_key)
        
        if tenant is None:
            try:
                from .models import Tenant
                tenant = Tenant.objects.select_related().get(
                    subdomain=subdomain,
                    is_active=True
                )
                # حفظ في الـ cache لمدة 15 دقيقة
                cache.set(cache_key, tenant, 900)
                logger.info(f"تم تحميل العميل من قاعدة البيانات: {subdomain}")
            except Tenant.DoesNotExist:
                # حفظ None في الـ cache لتجنب الاستعلامات المتكررة
                cache.set(cache_key, None, 300)
                logger.warning(f"عميل غير موجود: {subdomain}")
                return None
        
        # التحقق من حالة الاشتراك
        if not self.is_tenant_accessible(tenant):
            logger.warning(f"عميل غير متاح: {subdomain} - الحالة: {tenant.subscription_status}")
            return None
        
        return tenant
    
    def extract_subdomain(self, host):
        """استخراج الـ subdomain من اسم المضيف"""
        # إزالة البورت إن وجد
        host = host.split(':')[0]
        
        # تجاهل www
        if host.startswith('www.'):
            host = host[4:]
        
        parts = host.split('.')
        if len(parts) >= 3:  # subdomain.domain.com
            return parts[0]
        elif len(parts) == 2 and settings.DEBUG:  # للتطوير المحلي
            return parts[0] if parts[0] != 'localhost' else None
        
        return None
    
    def is_tenant_accessible(self, tenant):
        """فحص إذا كان العميل متاح للوصول"""
        if not tenant or not tenant.is_active:
            return False
        
        # فحص حالة الاشتراك
        if tenant.subscription_status in ['cancelled', 'suspended']:
            return False
        
        # فحص انتهاء فترة التجربة أو الاشتراك
        from django.utils import timezone
        now = timezone.now()
        
        if tenant.subscription_status == 'trial' and tenant.trial_ends_at:
            if now > tenant.trial_ends_at:
                return False
        
        if tenant.subscription_ends_at and now > tenant.subscription_ends_at:
            return False
        
        return True
    
    def is_excluded_path(self, path):
        """المسارات المستثناة من فحص العميل"""
        excluded_paths = [
            '/admin/',
            '/api/health/',
            '/api/signup/',
            '/static/',
            '/media/',
        ]
        return any(path.startswith(excluded) for excluded in excluded_paths)
    
    def activate_tenant(self, tenant):
        """تفعيل سياق العميل الحالي"""
        from threading import local
        if not hasattr(self, '_thread_locals'):
            self._thread_locals = local()
        self._thread_locals.tenant = tenant
    
    def deactivate_tenant(self):
        """إلغاء تفعيل سياق العميل"""
        if hasattr(self, '_thread_locals'):
            self._thread_locals.tenant = None

# managers.py - مدير مخصص للنماذج
from django.db import models
from threading import local

_thread_locals = local()

def get_current_tenant():
    """الحصول على العميل الحالي من thread-local storage"""
    return getattr(_thread_locals, 'tenant', None)

class TenantManager(models.Manager):
    """
    مدير مخصص يضيف تصفية تلقائية حسب العميل
    ويمنع الوصول لبيانات عملاء آخرين بالخطأ
    """
    
    def get_queryset(self):
        """إضافة تصفية العميل تلقائياً لكل الاستعلامات"""
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        
        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset.none()  # إرجاع queryset فارغ إذا لم يكن هناك عميل
    
    def create(self, **kwargs):
        """إضافة العميل الحالي تلقائياً عند الإنشاء"""
        tenant = get_current_tenant()
        if tenant and 'tenant' not in kwargs:
            kwargs['tenant'] = tenant
        return super().create(**kwargs)

# استخدام المدير المخصص في النماذج
class Product(TenantMixin):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # استخدام المدير المخصص
    objects = TenantManager()
    
    class Meta:
        unique_together = [['tenant', 'sku']]

# permissions.py - نظام صلاحيات محسّن
from rest_framework.permissions import BasePermission

class TenantPermission(BasePermission):
    """
    صلاحية تتحقق من:
    1. وجود عميل صالح
    2. انتماء المستخدم للعميل
    3. الصلاحيات المطلوبة
    """
    
    def has_permission(self, request, view):
        # التحقق من وجود العميل
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        
        # التحقق من تسجيل دخول المستخدم
        if not request.user.is_authenticated:
            return False
        
        # التحقق من انتماء المستخدم للعميل
        try:
            tenant_user = request.user.tenant_users.get(
                tenant=request.tenant,
                is_active=True
            )
            # حفظ معلومات المستخدم في الطلب
            request.tenant_user = tenant_user
            return True
        except:
            return False
    
    def has_object_permission(self, request, view, obj):
        # التحقق من أن الكائن ينتمي لنفس العميل
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.tenant
        return True

class FeaturePermission(BasePermission):
    """صلاحية للتحقق من الميزات المتاحة للعميل"""
    
    required_feature = None
    
    def has_permission(self, request, view):
        if not self.required_feature:
            return True
        
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        
        return request.tenant.has_feature(self.required_feature)

# views.py - مثال على استخدام النظام
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
@permission_classes([TenantPermission])
def get_products(request):
    """
    الحصول على المنتجات - سيتم تصفيتها تلقائياً حسب العميل
    بفضل TenantManager
    """
    products = Product.objects.all()  # سيتم تصفيتها تلقائياً
    
    # التحقق من الحدود
    if not request.tenant.is_within_limits('products'):
        return Response({
            'error': 'تم الوصول للحد الأقصى من المنتجات'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # تسلسل البيانات وإرسالها
    data = [{'id': p.id, 'name': p.name, 'price': str(p.price)} for p in products]
    return Response(data)

# الاستراتيجية الثانية: Schema-based Multi-Tenancy (للتطبيقات الكبيرة)
# =======================================================================

class SchemaBasedTenantRouter:
    """
    نهج أكثر تطوراً يستخدم PostgreSQL Schemas
    كل عميل له schema منفصل في نفس قاعدة البيانات
    """
    
    def __init__(self):
        self.tenant_schema_map = {}
    
    def db_for_read(self, model, **hints):
        tenant = self.get_current_tenant()
        if tenant:
            schema_name = f"tenant_{tenant.id}"
            # تعيين الـ schema الحالي
            self.set_schema(schema_name)
        return 'default'
    
    def set_schema(self, schema_name):
        """تغيير الـ schema الحالي في PostgreSQL"""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name}, public")

# الاستراتيجية الثالثة: Hybrid Approach (للتطبيقات المعقدة)
# ==============================================================

class HybridTenantStrategy:
    """
    نهج مختلط يجمع بين الاستراتيجيات:
    - العملاء الصغار: Single Database
    - العملاء الكبار: Database per Tenant
    - العملاء المؤسسيين: Dedicated Infrastructure
    """
    
    def get_tenant_strategy(self, tenant):
        if tenant.plan == 'enterprise':
            return 'dedicated_database'
        elif tenant.plan in ['premium'] and tenant.monthly_revenue > 10000:
            return 'separate_schema'
        else:
            return 'shared_database'
    
    def route_tenant_request(self, tenant, request):
        strategy = self.get_tenant_strategy(tenant)
        
        if strategy == 'dedicated_database':
            return self.handle_dedicated_database(tenant, request)
        elif strategy == 'separate_schema':
            return self.handle_separate_schema(tenant, request)
        else:
            return self.handle_shared_database(tenant, request)