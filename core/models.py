# # from django.db import models

# # # Create your models here.
# # class Tenant(models.Model):
# #     name = models.CharField(max_length=100)
# #     subdomain = models.CharField(max_length=100, unique=True)
# #     db_name = models.CharField(max_length=100)
# #     created_at = models.DateTimeField(auto_now_add=True)




# # models.py - نماذج إدارة العملاء
# from django.db import models
# from django.contrib.auth.models import AbstractUser
# from django.contrib.auth import get_user_model
# User = get_user_model()
# # class CustomUser(AbstractUser):
# #     """Custom user model that extends Django's default User model"""
# #     pass

# class Tenant(models.Model):
#     """نموذج العميل الأساسي"""
#     name = models.CharField(max_length=100)
#     subdomain = models.CharField(max_length=50, unique=True)
#     database_name = models.CharField(max_length=100)
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_active = models.BooleanField(default=True)
    
#     # إعدادات العميل
#     plan = models.CharField(max_length=20, choices=[
#         ('basic', 'Basic'),
#         ('premium', 'Premium'),
#         ('enterprise', 'Enterprise')
#     ])
#     max_users = models.IntegerField(default=5)
#     max_products = models.IntegerField(default=1000)
    
#     def __str__(self):
#         return self.name

# class UserTenant(models.Model):
#     """ربط المستخدمين بالعملاء"""
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
#     role = models.CharField(max_length=20, choices=[
#         ('admin', 'Admin'),
#         ('manager', 'Manager'),
#         ('employee', 'Employee')
#     ])
    
#     class Meta:
#         unique_together = ('user', 'tenant')
        
#     def __str__(self):
#         return f"{self.user.username} - {self.tenant.name}"

from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=50, unique=True)
    db_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
