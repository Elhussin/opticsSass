
# models/inventory.py - إدارة المخزون
class Supplier(models.Model):
    """الموردين"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Stock(models.Model):
    """مخزون المنتجات"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock')
    quantity_on_hand = models.IntegerField(default=0)
    quantity_reserved = models.IntegerField(default=0)  # محجوز للطلبات
    reorder_point = models.IntegerField(default=10)  # نقطة إعادة الطلب
    max_stock_level = models.IntegerField(default=100)
    
    # تتبع التكلفة
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    @property
    def available_quantity(self):
        """الكمية المتاحة للبيع"""
        return self.quantity_on_hand - self.quantity_reserved
    
    @property
    def needs_reorder(self):
        """هل يحتاج إعادة طلب؟"""
        return self.available_quantity <= self.reorder_point

class StockMovement(models.Model):
    """حركات المخزون"""
    MOVEMENT_TYPES = [
        ('in', 'دخول'),
        ('out', 'خروج'),
        ('adjustment', 'تعديل'),
        ('transfer', 'تحويل')
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)  # رقم الفاتورة أو الطلب
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"
