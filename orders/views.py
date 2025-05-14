# ecommerce/views.py

from decimal import Decimal
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from carts.models import Cart
from .models import Product, Order, OrderItem
from discounts.models import DiscountRule
from .serializers import (
    OrderSerializer, DiscountRuleSerializer, OrderCreateSerializer
)
from discounts.engine import DiscountEngine
from discounts.cache import invalidate_discount_rules_cache
import logging

logger = logging.getLogger(__name__)

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow users to view only their own orders,
    and admins to see all orders
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user

class OrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_orders(self, user):
        """Helper to fetch orders based on user role."""
        if user.is_staff:
            orders = Order.objects.all().prefetch_related('items', 'applied_discounts')
            logger.info(f"Staff user {user.id} retrieved all orders.")
        else:
            orders = Order.objects.filter(user=user).prefetch_related('items', 'applied_discounts')
            logger.info(f"Non-staff user {user.id} retrieved their orders.")
        
        return orders

    def get(self, request):
        """Retrieve a list of orders."""
        try:
            orders = self.get_orders(request.user)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving orders for user {request.user.id}: {e}")
            return Response({"error": "An error occurred while fetching orders."}, status=500)


class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_order(self, pk, user):
        """Helper to get the order based on user role."""
        if user.is_staff:
            order = get_object_or_404(Order.objects.prefetch_related('items', 'applied_discounts'), pk=pk)
            logger.info(f"Staff user {user.id} retrieved order {pk}.")
        else:
            order = get_object_or_404(Order.objects.prefetch_related('items', 'applied_discounts'), pk=pk, user=user)
            logger.info(f"Non-staff user {user.id} retrieved their order {pk}.")
        
        return order

    def get(self, request, pk):
        """Retrieve order details."""
        try:
            order = self.get_order(pk, request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving order {pk} for user {request.user.id}: {e}")
            return Response({"error": "An error occurred while fetching the order."}, status=500)


class DiscountRuleListAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Retrieve all discount rules."""
        try:
            discount_rules = DiscountRule.objects.all()
            serializer = DiscountRuleSerializer(discount_rules, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving discount rules: {e}")
            return Response({"error": "An error occurred while fetching discount rules."}, status=500)
    
    def post(self, request):
        """Create a new discount rule."""
        try:
            serializer = DiscountRuleSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                invalidate_discount_rules_cache()
                logger.info(f"Discount rule created successfully.")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating discount rule: {e}")
            return Response({"error": "An error occurred while creating the discount rule."}, status=500)


class DiscountRuleDetailAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, pk):
        """Retrieve a single discount rule."""
        try:
            discount_rule = get_object_or_404(DiscountRule, pk=pk)
            serializer = DiscountRuleSerializer(discount_rule)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving discount rule {pk}: {e}")
            return Response({"error": "An error occurred while fetching the discount rule."}, status=500)
    
    def put(self, request, pk):
        """Update a discount rule."""
        try:
            discount_rule = get_object_or_404(DiscountRule, pk=pk)
            serializer = DiscountRuleSerializer(discount_rule, data=request.data)
            if serializer.is_valid():
                serializer.save()
                invalidate_discount_rules_cache()
                logger.info(f"Discount rule {pk} updated successfully.")
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating discount rule {pk}: {e}")
            return Response({"error": "An error occurred while updating the discount rule."}, status=500)
    
    def delete(self, request, pk):
        """Delete a discount rule."""
        try:
            discount_rule = get_object_or_404(DiscountRule, pk=pk)
            discount_rule.delete()
            invalidate_discount_rules_cache()
            logger.info(f"Discount rule {pk} deleted successfully.")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting discount rule {pk}: {e}")
            return Response({"error": "An error occurred while deleting the discount rule."}, status=500)


class OrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Create a new order from cart items."""
        user = request.user
        cart_items = Cart.objects.select_related('product').filter(user=user)

        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate product availability
        for cart_item in cart_items:
            product = cart_item.product
            if product.stock_quantity < cart_item.quantity:
                return Response(
                    {"error": f"Not enough stock for {product.name}. Available: {product.stock_quantity}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Calculate total amount
        total_amount = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)

        # Create Order
        try:
            order = Order.objects.create(
                user=user,
                total_amount=total_amount,
                discounted_amount=total_amount  # will be updated after discounts
            )

            # Create OrderItems and update product stock
            for cart_item in cart_items:
                product = cart_item.product
                quantity = cart_item.quantity

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                    discounted_price=product.price  # will be updated by discount engine
                )

                product.stock_quantity -= quantity
                product.save()

            # Apply discounts
            discount_engine = DiscountEngine(order, user)
            updated_order = discount_engine.calculate_discounts()

            # Clear cart after placing order
            cart_items.delete()

            # Return order details
            serializer = OrderSerializer(updated_order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating order for user {user.id}: {e}")
            return Response({"error": "An error occurred while placing the order."}, status=500)