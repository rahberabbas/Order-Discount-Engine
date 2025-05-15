from base64 import b64encode
from io import BytesIO
from PIL import Image
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Category, Product

User = get_user_model()

class CategoryTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", password="adminpass", is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_create_category(self):
        url = reverse('category-list-create')  # Adjust this to your path name
        data = {"name": "Electronics", "description": "Gadgets and devices"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Category.objects.count(), 1)

    def test_get_categories(self):
        Category.objects.create(name="Books")
        url = reverse('category-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_update_category(self):
        category = Category.objects.create(name="Toys")
        url = reverse('category-detail', args=[category.id])
        response = self.client.put(url, {"name": "Updated Toys"})
        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.name, "Updated Toys")

    def test_delete_category(self):
        category = Category.objects.create(name="Shoes")
        url = reverse('category-detail', args=[category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

def get_base64_test_image():
    buffer = BytesIO()
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(buffer, format="JPEG")
    return b64encode(buffer.getvalue()).decode()

class ProductTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", password="adminpass", is_staff=True)
        self.client = APIClient()
        self.category = Category.objects.create(name="Electronics")
        self.product_data = {
            "name": "Laptop",
            "description": "High performance",
            "price": 1500.00,
            "stock_quantity": 10,
            "category": self.category.id,
            "thumbnail_image": get_base64_test_image(),
            "products_image": [{"image": get_base64_test_image()}]
        }

    def test_get_product_list(self):
        Product.objects.create(
            name="TV", description="Smart TV", price=1000,
            category=self.category, stock_quantity=5
        )
        url = reverse('product-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_update_product(self):
        self.client.force_authenticate(user=self.admin)
        product = Product.objects.create(
            name="Phone", description="Android", price=300,
            category=self.category, stock_quantity=20
        )
        url = reverse('product-detail', args=[product.slug])
        response = self.client.put(url, {
            "name": "Smartphone",
            "description": "Updated Android phone",
            "price": 350,
            "stock_quantity": 15,
            "category": self.category.id
        }, format='json')
        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.name, "Smartphone")

    def test_delete_product(self):
        self.client.force_authenticate(user=self.admin)
        product = Product.objects.create(
            name="Watch", description="Smartwatch", price=200,
            category=self.category, stock_quantity=10
        )
        url = reverse('product-detail', args=[product.slug])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)