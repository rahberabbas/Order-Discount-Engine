from django.contrib import admin
from .models import Order, OrderItem
from discounts.models import AppliedDiscount, DiscountRule

# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('unit_price', 'discounted_price', 'subtotal', 'discounted_subtotal')


class AppliedDiscountInline(admin.TabularInline):
    model = AppliedDiscount
    extra = 0
    readonly_fields = ('discount_name', 'description', 'amount')
    can_delete = False
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'discounted_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('total_amount', 'discounted_amount')
    inlines = [OrderItemInline, AppliedDiscountInline]