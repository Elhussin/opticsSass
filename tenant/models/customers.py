
# models/customers.py - إدارة العملاء
class Customer(models.Model):
    """عملاء المتجر"""
    # معلومات شخصية
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # العنوان
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # معلومات العضوية
    customer_since = models.DateTimeField(auto_now_add=True)
    is_vip = models.BooleanField(default=False)
    loyalty_points = models.IntegerField(default=0)
    
    # إعدادات التسويق
    accepts_marketing = models.BooleanField(default=True)
    preferred_contact = models.CharField(max_length=10, choices=[
        ('email', 'بريد إلكتروني'),
        ('phone', 'هاتف'),
        ('sms', 'رسائل نصية')
    ], default='email')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class PrescriptionRecord(models.Model):
    """سجلات الوصفة الطبية"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='prescriptions')
    
    # معلومات العين اليمنى
    right_sphere = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    right_cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    right_axis = models.IntegerField(null=True, blank=True)
    
    # معلومات العين اليسرى
    left_sphere = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    left_cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    left_axis = models.IntegerField(null=True, blank=True)
    
    # معلومات إضافية
    pupillary_distance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    doctor_name = models.CharField(max_length=200, blank=True)
    prescription_date = models.DateField()
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # الوصفة الحالية
    
    def __str__(self):
        return f"وصفة {self.customer.full_name} - {self.prescription_date}"