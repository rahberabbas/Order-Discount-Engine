from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class AuthTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')  # You must map this name in urls.py
        self.login_url = reverse('login')
        self.token_refresh_url = reverse('token_refresh')

        self.user_data = {
            "email": "testuser@example.com",
            "password": "strongpassword123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+911234567890"
        }

        self.user = User.objects.create_user(**self.user_data)

    def test_register_user_success(self):
        response = self.client.post(self.register_url, {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
            "phone": "+919876543210"
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["message"], "User created successfully")

    def test_register_user_email_already_exists(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["errors"])

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["message"], "Login successful")

    def test_login_invalid_password(self):
        response = self.client.post(self.login_url, {
            "email": self.user_data["email"],
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid login credentials")

    def test_token_refresh_success(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(self.token_refresh_url, {
            "refresh": str(refresh)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid_token(self):
        response = self.client.post(self.token_refresh_url, {
            "refresh": "invalidtoken"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

