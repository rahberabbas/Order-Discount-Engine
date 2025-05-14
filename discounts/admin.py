# ecommerce/admin.py

from django.contrib import admin
from .models import DiscountRule, AppliedDiscount
from .cache import invalidate_discount_rules_cache

class AppliedDiscountInline(admin.TabularInline):
    model = AppliedDiscount
    extra = 0
    readonly_fields = ('discount_name', 'description', 'amount')
    can_delete = False



@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'priority', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'discount_type', 'priority', 'is_active')
        }),
        ('Percentage Discount Settings', {
            'fields': ('min_order_value', 'percentage'),
            'classes': ('collapse',),
            'description': 'Settings for percentage-based discounts on total order value'
        }),
        ('Flat Discount Settings', {
            'fields': ('min_previous_orders', 'flat_amount'),
            'classes': ('collapse',),
            'description': 'Settings for flat discounts based on customer order history'
        }),
        ('Category Discount Settings', {
            'fields': ('category', 'min_items_in_category', 'category_discount_percentage'),
            'classes': ('collapse',),
            'description': 'Settings for discounts based on product categories'
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Invalidate cache when discount rules are changed"""
        super().save_model(request, obj, form, change)
        invalidate_discount_rules_cache()
    
    def delete_model(self, request, obj):
        """Invalidate cache when discount rules are deleted"""
        super().delete_model(request, obj)
        invalidate_discount_rules_cache()