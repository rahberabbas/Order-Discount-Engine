from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from products.models import Product, Category
from .models import Cart

User = get_user_model()

class CartAPITestCase(APITestCase):
    def setUp(self):
        # Create user and authenticate
        self.user = User.objects.create_user(
            email="newuser@example.com",
            password="newpassword123",
            first_name="New",
            last_name="User",
            phone="+919876543210"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create category and product
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="iPhone 15",
            description="Latest iPhone model",
            price=999.99,
            stock_quantity=10,
            category=self.category,
            is_active=True
        )

    def test_add_product_to_cart(self):
        url = reverse("cart-list-create")  # Set this as the route name in urls.py
        response = self.client.post(url, {
            "product": self.product.id,
            "quantity": 2
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 2)
        self.assertEqual(Cart.objects.count(), 1)

    def test_add_product_insufficient_stock(self):
        url = reverse("cart-list-create")
        response = self.client.post(url, {
            "product": self.product.id,
            "quantity": 100  # Exceeds stock
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only", response.data['error'])

    def test_get_cart_items(self):
        Cart.objects.create(user=self.user, product=self.product, quantity=2)
        url = reverse("cart-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cart_items']), 1)

    def test_increase_cart_item_quantity(self):
        cart_item = Cart.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse("cart-increase-quantity", kwargs={"pk": cart_item.pk})  # Set this route name
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 2)

    def test_decrease_cart_item_quantity(self):
        cart_item = Cart.objects.create(user=self.user, product=self.product, quantity=2)
        url = reverse("cart-decrease-quantity", kwargs={"pk": cart_item.pk})  # Set this route name
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 1)

    def test_decrease_cart_to_zero_deletes_item(self):
        cart_item = Cart.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse("cart-decrease-quantity", kwargs={"pk": cart_item.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Cart.objects.count(), 0)

    def test_delete_cart_item(self):
        cart_item = Cart.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse("cart-detail", kwargs={"pk": cart_item.pk})  # Set this route name
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Cart.objects.count(), 0)
