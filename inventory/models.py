from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

user = get_user_model()

class Supplier(models.Model):
    """
    Docstring for Supplier
    Represent companies that supply products
    """

    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: 
        ordering = ['name']
    
    def __str__(self):
        return self.name