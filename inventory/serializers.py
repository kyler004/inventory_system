from rest_framework import serializers
from django.db import transaction
from .models import Supplier, Product, StockMovement

class SupplierSerializer(serializers.ModelSerializer):
    """ Serializer for Supplier Model"""

    # Add computed field showing product count
    product_count = serializers.IntegerField(read_only=True, source='products.count')

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_person', 'email', 
            'phone', 'address', 'product_count',
            'created_at' ,'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_email(self, value):
        """Custom validation for email"""
        if value and not '@' in value:
            raise serializers.ValidationError("Invalid email format")
        return value.lower()

class ProductListSerializer(serializers.ModelSerializer):
    """
    Docstring for ProductListSerializer
    Lightweight serializer for product lists
    Shows minimal info for performance
    """

    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name' ,'sku', 'supplier_name',
            'current_stock', 'minimum_stock', 'is_low_stock', 
            'unit_price'
        ]
