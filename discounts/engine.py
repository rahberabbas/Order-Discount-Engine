# ecommerce/discount_engine.py

from decimal import Decimal
import logging
from django.db.models import Count

from carts.models import Cart
from .models import  AppliedDiscount, DiscountRule
from orders.models import Order, OrderItem
from products.models import Product
from .cache import get_discount_rules_from_cache

logger = logging.getLogger(__name__)

class DiscountEngine:
    def __init__(self, order, user):
        self.order = order
        self.user = user
        if self.order is not None:
            self.order_items = list(order.items.all().select_related('product'))
            self.total_amount = sum(item.unit_price * item.quantity for item in self.order_items)
            self.discounted_amount = self.total_amount
            self.applied_discounts = []
        
        self.cart_items = list(Cart.objects.filter(user=self.user).select_related('product'))
        self.cart_total_amount = sum(item.product.price * item.quantity for item in self.cart_items)
        self.discounted_cart_amount = self.cart_total_amount
        self.applied_cart_discounts = []
        
    def get_cart_items(self):
        cart = Cart.objects.filter(user=self.user)
        # print(cart)
        discount_rules = get_discount_rules_from_cache()
        for rule in discount_rules:
            if rule.is_active:
                if rule.discount_type == 'percentage':
                    self._apply_cart_percentage_discount(rule)
                elif rule.discount_type == 'flat':
                    self._apply_cart_flat_discount(rule)
                elif rule.discount_type == 'category':
                    self._apply_cart_category_discount(rule)
        
        return {
            "applied_discounts": self.applied_cart_discounts  # now just a list of dicts
            }
        
    def _apply_cart_percentage_discount(self, rule):
        """Apply percentage discount if total order value exceeds threshold"""
        if self.cart_total_amount >= rule.min_order_value:
            
            discount_amount = self.discounted_cart_amount * (rule.percentage / Decimal('100'))
            new_discounted_amount = self.discounted_cart_amount - discount_amount
            
            # Append dictionary instead of creating model
            self.applied_cart_discounts.append({
                "discount_rule_id": rule.id if hasattr(rule, 'id') else None,
                "discount_name": f"{rule.percentage}% Discount",
                "description": f"Order value exceeds ₹{rule.min_order_value}",
                "amount": discount_amount
            })
            
            self.discounted_cart_amount = new_discounted_amount
            logger.info(f"Applied {rule.percentage}% discount: ₹{discount_amount}")
            
    def _apply_cart_flat_discount(self, rule):
        """Apply flat discount if user has placed enough previous orders"""
        previous_orders_count = Order.objects.filter(
            user=self.user, 
        ).count()
        
        if previous_orders_count >= rule.min_previous_orders:
            # Don't discount more than the order value
            discount_amount = min(rule.flat_amount, self.discounted_cart_amount)
            new_discounted_amount = self.discounted_cart_amount - discount_amount
            
            # Create record of applied discount
            self.applied_cart_discounts.append({
                "discount_rule_id": rule.id if hasattr(rule, 'id') else None,
                "discount_name": "Loyal Customer Discount",
                "description": f"Flat discount for having {previous_orders_count} previous orders",
                "amount": discount_amount
            })
            
            self.discounted_cart_amount = new_discounted_amount
            logger.info(f"Applied flat discount: ₹{discount_amount}")
            
    def _apply_cart_category_discount(self, rule):
        """
        Apply discount for items in a specific category in the cart
        if the user buys more than the minimum quantity.
        """

        target_category = rule.category
        category_counts = 0

        # Count previous orders in the same category
        previous_orders = Order.objects.filter(user=self.user)
        for order in previous_orders:
            for item in order.items.all():
                if item.product.category == target_category:
                    category_counts += item.quantity

        # Count current cart items in the same category
        for item in self.cart_items:
            if item.product.category == target_category:
                category_counts += item.quantity

        # If minimum threshold met, apply category discount
        if category_counts > rule.min_items_in_category:
            total_category_discount = Decimal('0')

            # Iterate through cart items to calculate discount
            for item in self.cart_items:
                if item.product.category == target_category:
                    item_original_total = item.product.price * item.quantity
                    item_discount = item_original_total * (rule.category_discount_percentage / Decimal('100'))

                    # Attach discounted_price dynamically (not saved to DB)
                    item.discounted_price = item.product.price - (
                        item.product.price * rule.category_discount_percentage / Decimal('100')
                    )

                    total_category_discount += item_discount

            if total_category_discount > 0:
                self.applied_cart_discounts.append({
                    "rule_id": rule.id,
                    "discount_name": f"Category Discount on {target_category.name}",
                    "description": f"{rule.category_discount_percentage}% off on {target_category.name} items",
                    "amount": total_category_discount
                })

                self.discounted_cart_amount -= total_category_discount
                logger.info(f"Applied category discount: ₹{total_category_discount}")


        
    def calculate_discounts(self):
        """Apply all eligible discounts to the order"""
        # Get discount rules from cache or DB, sorted by priority
        discount_rules = get_discount_rules_from_cache()
        
        # Apply each discount rule in priority order
        for rule in discount_rules:
            if rule.is_active:
                if rule.discount_type == 'percentage':
                    self._apply_percentage_discount(rule)
                elif rule.discount_type == 'flat':
                    self._apply_flat_discount(rule)
                elif rule.discount_type == 'category':
                    self._apply_category_discount(rule)
        
        # Update order with discounted amount
        self.order.total_amount = self.total_amount
        self.order.discounted_amount = self.discounted_amount
        self.order.save()
        
        # Save applied discounts
        AppliedDiscount.objects.bulk_create(self.applied_discounts)
        
        return self.order

    def _apply_percentage_discount(self, rule):
        """Apply percentage discount if total order value exceeds threshold"""
        if self.total_amount >= rule.min_order_value:
            print("Total amount", self.total_amount, "  ", rule.min_order_value, "  ", self.discounted_amount)
            discount_amount = self.discounted_amount * (rule.percentage / Decimal('100'))
            new_discounted_amount = self.discounted_amount - discount_amount
            
            # Create record of applied discount
            self.applied_discounts.append(
                AppliedDiscount(
                    order=self.order,
                    discount_rule=rule,
                    discount_name=f"{rule.percentage}% Discount",
                    description=f"Order value exceeds ₹{rule.min_order_value}",
                    amount=discount_amount
                )
            )
            
            self.discounted_amount = new_discounted_amount
            logger.info(f"Applied {rule.percentage}% discount: ₹{discount_amount}")

    def _apply_flat_discount(self, rule):
        """Apply flat discount if user has placed enough previous orders"""
        previous_orders_count = Order.objects.filter(
            user=self.user, 
        ).count()
        
        if previous_orders_count >= rule.min_previous_orders:
            # Don't discount more than the order value
            discount_amount = min(rule.flat_amount, self.discounted_amount)
            new_discounted_amount = self.discounted_amount - discount_amount
            
            # Create record of applied discount
            self.applied_discounts.append(
                AppliedDiscount(
                    order=self.order,
                    discount_rule=rule,
                    discount_name="Loyal Customer Discount",
                    description=f"Flat discount for having {previous_orders_count} previous orders",
                    amount=discount_amount
                )
            )
            
            self.discounted_amount = new_discounted_amount
            logger.info(f"Applied flat discount: ₹{discount_amount}")

    def _apply_category_discount(self, rule):
        """Apply discount for items in a specific category if the user buys more than the minimum quantity from that category."""
        
        # Ensure the discount is applied to the right category from the DB
        target_category = rule.category  # This comes from DB, so rule.category will give us the right category

        # Initialize a count for the target category items
        category_counts = 0
        
        # Include previous orders in the count for the specific category
        previous_orders = Order.objects.filter(user=self.user)
        for order in previous_orders:
            for item in order.items.all():
                if item.product.category == target_category:  # Filter only items in the target category
                    category_counts += item.quantity
        
        # Add current order items to the category count
        for item in self.order_items:
            if item.product.category == target_category:  # Filter only items in the target category
                category_counts += item.quantity
        
        # Check if the total items in the target category exceed the minimum threshold
        if category_counts > rule.min_items_in_category:
            total_category_discount = Decimal('0')

            # Apply the discount to each item of the target category in the current order
            for item in self.order_items:
                if item.product.category == target_category:  # Only apply to the target category items
                    item_original_total = item.unit_price * item.quantity
                    item_discount = item_original_total * (rule.category_discount_percentage / Decimal('100'))
                    
                    # Apply the discount to the unit price
                    new_unit_price = item.unit_price - (item.unit_price * rule.category_discount_percentage / Decimal('100'))
                    item.discounted_price = new_unit_price
                    item.save()
                    
                    total_category_discount += item_discount
            
            # Only create a discount record if some discount was applied
            if total_category_discount > 0:
                self.applied_discounts.append(
                    AppliedDiscount(
                        order=self.order,
                        discount_rule=rule,
                        discount_name=f"Category Discount on {target_category.name}",
                        description=f"{rule.category_discount_percentage}% off on {target_category.name} items",
                        amount=total_category_discount
                    )
                )
                
                self.discounted_amount -= total_category_discount
                logger.info(f"Applied category discount: ₹{total_category_discount}")
