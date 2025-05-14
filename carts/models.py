from django.db import models
from django.conf import settings
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name_plural = "UserCarts"  # Admin display name

    def __str__(self):
        return f"{self.user.first_name}'s cart - {self.product.name} (x{self.quantity})"

    def get_total_price(self):
        return self.quantity * self.product.price