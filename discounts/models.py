from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from orders.models import Order
from products.models import Category

User = get_user_model()

# Create your models here.
class DiscountRule(models.Model):
    """Model to store configurable discount rules"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('flat', 'Flat Discount'),
        ('category', 'Category-Based Discount'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    
    # For percentage discounts
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, 
                                       validators=[MinValueValidator(0)], null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, 
                                  validators=[MinValueValidator(0), MaxValueValidator(100)], 
                                  null=True, blank=True)
    
    # For flat discounts
    min_previous_orders = models.PositiveIntegerField(null=True, blank=True)
    flat_amount = models.DecimalField(max_digits=10, decimal_places=2, 
                                    validators=[MinValueValidator(0)], null=True, blank=True)
    
    # For category-based discounts
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    min_items_in_category = models.PositiveIntegerField(null=True, blank=True)
    category_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, 
                                                    validators=[MinValueValidator(0), MaxValueValidator(100)], 
                                                    null=True, blank=True)
    
    # Priority for stackable discounts (lower number = higher priority)
    priority = models.PositiveIntegerField(default=1)
    
    # Is the discount active?
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
class AppliedDiscount(models.Model):
    """Record of discounts applied to orders"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='applied_discounts')
    discount_rule = models.ForeignKey(DiscountRule, on_delete=models.SET_NULL, null=True)
    discount_name = models.CharField(max_length=100)  # Kept even if rule is deleted
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return f"{self.discount_name} (₹{self.amount}) on Order #{self.order.id}"