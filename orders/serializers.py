# ecommerce/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User

from accounts.serializers import UserSerializer
from products.serializers import ProductSerializer
from .models import  Order, OrderItem
from discounts.models import DiscountRule, AppliedDiscount


class DiscountRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountRule
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_details', 'quantity', 'unit_price', 
                  'discounted_price', 'subtotal', 'discounted_subtotal']
        read_only_fields = ['unit_price', 'discounted_price', 'subtotal', 'discounted_subtotal']


class AppliedDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppliedDiscount
        fields = ['id', 'discount_name', 'description', 'amount']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    applied_discounts = AppliedDiscountSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_amount', 'discounted_amount', 
                  'items', 'applied_discounts', 'created_at', 'updated_at']
        read_only_fields = ['total_amount', 'discounted_amount', 'applied_discounts', 'user']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
            
        return order


# class OrderCreateSerializer(serializers.Serializer):
#     items = serializers.ListField(
#         child=serializers.DictField(
#             child=serializers.IntegerField(),
#             keys={
#                 'product_id': serializers.IntegerField(),
#                 'quantity': serializers.IntegerField(min_value=1)
#             }
#         )
#     )

class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class OrderCreateSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=OrderItemInputSerializer()
    )
