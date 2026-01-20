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

class Product(models.Model):
    """
    Docstring for Product
    Represents items in inventory
    """
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    description = models.TextField(blank=True)
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT,
        related_name='products'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    current_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current quantity in stock"
    )
    minimum_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Alert when stock falls below this level"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def is_low_stock(self):
        """Check if product is below minimum stock level"""
        return self.current_stock <= self.minimum_stock
    
    @property
    def stock_value(self):
        """Calculate total value of current stock"""
        return self.current_stock * self.unit_price

class StockMovement(models.Model):
    """
    Records all stock changes (in/out) with transaction safety
    """
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    reference = models.CharField(
        max_length=100, 
        blank=True,
        help_text="PO number, invoice, etc."
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='stock_movements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Track stock before and after for audit trail
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.movement_type} - {self.product.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically update product stock
        This demonstrates transaction safety
        """
        # Record stock before change
        self.stock_before = self.product.current_stock
        
        # Calculate new stock based on movement type
        if self.movement_type == 'IN':
            self.product.current_stock += self.quantity
        elif self.movement_type == 'OUT':
            if self.product.current_stock < self.quantity:
                raise ValueError(
                    f"Insufficient stock. Available: {self.product.current_stock}, "
                    f"Requested: {self.quantity}"
                )
            self.product.current_stock -= self.quantity
        elif self.movement_type == 'ADJUSTMENT':
            self.product.current_stock = self.quantity
        
        # Record stock after change
        self.stock_after = self.product.current_stock
        
        # Save product first, then movement
        # If this is in a transaction, both will rollback on error
        self.product.save()
        super().save(*args, **kwargs)
