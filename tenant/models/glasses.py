# models/glasses.py - نماذج خاصة بالنظارات
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Brand(models.Model):
    """العلامات التجارية للنظارات"""
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    """فئات النظارات"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class FrameMaterial(models.Model):
    """مواد الإطار"""
    name = models.CharField(max_length=50)  # مثل: معدن، بلاستيك، تيتانيوم
    properties = models.JSONField(default=dict)  # خصائص المادة
    
    def __str__(self):
        return self.name

class LensType(models.Model):
    """أنواع العدسات"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """المنتج الأساسي (النظارة)"""
    GENDER_CHOICES = [
        ('unisex', 'للجميع'),
        ('men', 'رجالي'),
        ('women', 'نسائي'),
        ('kids', 'أطفال')
    ]
    
    FRAME_SHAPES = [
        ('round', 'دائري'),
        ('square', 'مربع'),
        ('rectangular', 'مستطيل'),
        ('aviator', 'طيار'),
        ('cat_eye', 'عين القطة'),
        ('oval', 'بيضاوي')
    ]
    
    # معلومات أساسية
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)  # رمز المنتج
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    # وصف المنتج
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=255, blank=True)
    
    # مواصفات الإطار
    frame_material = models.ForeignKey(FrameMaterial, on_delete=models.CASCADE)
    frame_shape = models.CharField(max_length=20, choices=FRAME_SHAPES)
    frame_color = models.CharField(max_length=50)
    frame_size = models.CharField(max_length=20)  # مثل: 52-18-140
    
    # مواصفات النظارة
    bridge_width = models.IntegerField(help_text="عرض الجسر بالمليمتر")
    lens_width = models.IntegerField(help_text="عرض العدسة بالمليمتر")
    temple_length = models.IntegerField(help_text="طول الذراع بالمليمتر")
    
    # معلومات التسويق
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
    age_group = models.CharField(max_length=20, blank=True)
    
    # التسعير
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # الحالة والتوفر
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    requires_prescription = models.BooleanField(default=False)
    
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # الصور
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    def __str__(self):
        return f"{self.brand.name} {self.name}"
    
    @property
    def current_price(self):
        """السعر الحالي (مع الخصم إن وجد)"""
        return self.discount_price if self.discount_price else self.selling_price
    
    @property
    def profit_margin(self):
        """هامش الربح"""
        return ((self.current_price - self.cost_price) / self.cost_price) * 100

class ProductImage(models.Model):
    """صور إضافية للمنتج"""
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']

class ProductVariant(models.Model):
    """أشكال مختلفة للمنتج (ألوان مختلفة مثلاً)"""
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.CharField(max_length=50)
    color_code = models.CharField(max_length=7, help_text="كود اللون الهكساديسيمال")
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sku_suffix = models.CharField(max_length=10)  # إضافة لرمز المنتج
    
    def __str__(self):
        return f"{self.product.name} - {self.color}"
