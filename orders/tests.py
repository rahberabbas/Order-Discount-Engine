from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from products.models import Product, Category
from carts.models import Cart
from discounts.models import DiscountRule, AppliedDiscount
from orders.models import Order, OrderItem

User = get_user_model()

class OrderCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            phone='+919999999999'
        )
        self.client.force_authenticate(user=self.user)

        # Create product category
        self.category = Category.objects.create(name="Electronics")

        # Create products
        self.product1 = Product.objects.create(
            name="Laptop", category=self.category, price=1000.00, stock_quantity=10
        )
        self.product2 = Product.objects.create(
            name="Mouse", category=self.category, price=50.00, stock_quantity=20
        )

        # Add products to cart
        Cart.objects.create(user=self.user, product=self.product1, quantity=1)
        Cart.objects.create(user=self.user, product=self.product2, quantity=2)

        # Create discount rules
        DiscountRule.objects.create(
            name="10% off orders over 500",
            description="10% discount for orders greater than 500",
            discount_type='percentage',
            min_order_value=500,
            percentage=10,
            priority=1,
            is_active=True
        )
        DiscountRule.objects.create(
            name="Category discount 5%",
            description="5% off on electronics if buying 2 or more items",
            discount_type='category',
            category=self.category,
            min_items_in_category=2,
            category_discount_percentage=5,
            priority=2,
            is_active=True
        )

    def test_order_creation_with_discounts(self):
        url = reverse('create-order')

        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn('id', data)
        self.assertIn('items', data)
        self.assertIn('applied_discounts', data)

        # Check that order items count matches cart items
        self.assertEqual(len(data['items']), 2)

        # Check if applied discounts exist
        self.assertTrue(len(data['applied_discounts']) > 0)

        # Verify product stock is updated
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()

        self.assertEqual(self.product1.stock_quantity, 9)  # 10 - 1
        self.assertEqual(self.product2.stock_quantity, 18)  # 20 - 2

        # Verify discounted amount < total amount due to discount applied
        total_amount = sum(Decimal(item['unit_price']) * int(item['quantity']) for item in data['items'])
        discounted_amount = Decimal(data['discounted_amount'])

        self.assertLess(discounted_amount, total_amount)

        # Verify AppliedDiscounts exist in DB for this order
        order = Order.objects.get(id=data['id'])
        applied_discounts = AppliedDiscount.objects.filter(order=order)
        self.assertTrue(applied_discounts.exists())

    def test_order_creation_fails_if_cart_empty(self):
        # Clear cart first
        Cart.objects.filter(user=self.user).delete()

        url = reverse('create-order')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], "Your cart is empty.")

    def test_order_creation_fails_if_stock_insufficient(self):
        # Set product stock to 0 to trigger failure
        self.product1.stock_quantity = 0
        self.product1.save()

        url = reverse('create-order')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Not enough stock", response.json()['error'])
