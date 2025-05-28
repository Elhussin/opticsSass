from django.db import models

# Create your models here.
class Tenant(models.Model):
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=100, unique=True)
    db_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)