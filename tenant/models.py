from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('sales', 'Sales'),
        ('tech', 'Technician'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
