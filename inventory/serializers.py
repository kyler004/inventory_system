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
class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Docstring for ProductDetailSerializer
    Detail serializer for single product view
    Includes rekated data and computed fields
    """
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryet=Supplier.objects.all(),
        source='supplier',
        write_only=True
    )
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_value = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    recent_movements = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description',
            'supplier', 'supplier_id', 'unit_price',
            'current_stock', 'minimum_stock', 
            'is_low_stock', 'stock_value',
            'recent_movements',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'current_stock']
    def get_recent_movements(self, obj):
        """Get last 5 stock movements for this product"""
        movements = obj.stock_movements.all()[:5]
        return StockMovementSerializer(movements, many=True).data
    
    def validate_sku(self, value):
        """Ensure SKU is uppercase and unique"""
        value = value.upper().strip()
        
        # Check uniqueness only on create or if SKU changed
        instance = self.instance
        if instance is None or instance.sku != value:
            if Product.objects.filter(sku=value).exists():
                raise serializers.ValidationError("SKU already exists")
        
        return value
    
    def validate(self, data):
        """
        Object-level validation
        Ensure minimum stock makes sense
        """
        minimum_stock = data.get('minimum_stock', 0)
        if minimum_stock < 0:
            raise serializers.ValidationError({
                'minimum_stock': 'Cannot be negative'
            })
        return data

