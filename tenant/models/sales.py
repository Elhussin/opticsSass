0
class Order(models.Model):
    """طلبات الشراء"""
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('confirmed', 'مؤكد'),
        ('processing', 'قيد التحضير'),
        ('ready', 'جاهز للاستلام'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('partial', 'دفع جزئي'),
        ('paid', 'مدفوع بالكامل'),
        ('refunded', 'مسترد'),
    ]
    
    # معلومات الطلب الأساسية
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='orders')
    
    # حالة الطلب
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # المبالغ المالية
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # معلومات إضافية
    notes = models.TextField(blank=True, help_text="ملاحظات خاصة بالطلب")
    internal_notes = models.TextField(blank=True, help_text="ملاحظات داخلية للموظفين فقط")
    
    # تواريخ مهمة
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    expected_delivery = models.DateTimeField(null=True, blank=True)
    
    # موظف المبيعات المسؤول
    sales_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"طلب {self.order_number} - {self.customer.full_name}"
    
    @property
    def remaining_amount(self):
        """المبلغ المتبقي للدفع"""
        return self.total_amount - self.paid_amount
    
    @property
    def is_fully_paid(self):
        """هل تم دفع الطلب بالكامل؟"""
        return self.paid_amount >= self.total_amount
    
    def save(self, *args, **kwargs):
        # إنشاء رقم طلب تلقائي إذا لم يكن موجوداً
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """إنشاء رقم طلب فريد"""
        import datetime
        today = datetime.date.today()
        # تنسيق: ORD-YYYYMMDD-XXXX
        prefix = f"ORD-{today.strftime('%Y%m%d')}"
        
        # البحث عن آخر رقم طلب لليوم الحالي
        last_order = Order.objects.filter(
            order_number__startswith=prefix
        ).order_by('-created_at').first()
        
        if last_order:
            # استخراج الرقم التسلسلي وزيادته
            last_number = int(last_order.order_number.split('-')[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        
        return f"{prefix}-{next_number:04d}"

class OrderItem(models.Model):
    """عناصر الطلب"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    
    # الكمية والأسعار
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # معلومات العدسات (إذا كانت مطلوبة)
    lens_type = models.ForeignKey('LensType', on_delete=models.SET_NULL, null=True, blank=True)
    prescription = models.ForeignKey('PrescriptionRecord', on_delete=models.SET_NULL, null=True, blank=True)
    
    # معلومات خاصة