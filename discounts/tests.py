from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from products.models import Category
from discounts.models import DiscountRule

User = get_user_model()

class DiscountRuleAPITestCase(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            phone='+919999999999'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

        self.category = Category.objects.create(name="Mobiles")

        self.valid_discount_data = {
            "name": "Summer Sale",
            "description": "10% off on orders above ₹1000",
            "discount_type": "percentage",
            "min_order_value": 1000,
            "percentage": 10,
            "priority": 1,
            "is_active": True
        }

    def test_list_discount_rules_empty(self):
        url = reverse("discount-rule-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_valid_percentage_discount_rule(self):
        url = reverse("discount-rule-list")
        response = self.client.post(url, data=self.valid_discount_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DiscountRule.objects.count(), 1)
        self.assertEqual(response.data['name'], "Summer Sale")

    def test_create_category_discount_rule(self):
        url = reverse("discount-rule-list")
        category_discount_data = {
            "name": "Mobiles Discount",
            "description": "5% off if you buy 2 or more phones",
            "discount_type": "category",
            "category": self.category.id,
            "min_items_in_category": 2,
            "category_discount_percentage": 5,
            "priority": 2,
            "is_active": True
        }
        response = self.client.post(url, data=category_discount_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["discount_type"], "category")

    def test_get_single_discount_rule(self):
        rule = DiscountRule.objects.create(**self.valid_discount_data)
        url = reverse("discount-rule-detail", kwargs={"pk": rule.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], rule.name)

    def test_update_discount_rule(self):
        rule = DiscountRule.objects.create(**self.valid_discount_data)
        url = reverse("discount-rule-detail", kwargs={"pk": rule.pk})
        updated_data = self.valid_discount_data.copy()
        updated_data['percentage'] = 15
        response = self.client.put(url, data=updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rule.refresh_from_db()
        self.assertEqual(rule.percentage, 15)

    def test_delete_discount_rule(self):
        rule = DiscountRule.objects.create(**self.valid_discount_data)
        url = reverse("discount-rule-detail", kwargs={"pk": rule.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DiscountRule.objects.filter(pk=rule.pk).exists())

    def test_create_invalid_discount_percentage_above_100(self):
        invalid_data = self.valid_discount_data.copy()
        invalid_data['percentage'] = 150  # Invalid
        url = reverse("discount-rule-list")
        response = self.client.post(url, data=invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('percentage', response.data)

    def test_permission_denied_for_non_admin_user(self):
        normal_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            first_name='Test',
            last_name='User',
            phone='+918888888888'
        )
        self.client.force_authenticate(user=normal_user)
        url = reverse("discount-rule-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
