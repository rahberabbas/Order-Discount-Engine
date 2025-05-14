from .models import Cart
from rest_framework import serializers

class CartSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.name')
    product_slug = serializers.ReadOnlyField(source='product.slug')
    price = serializers.ReadOnlyField(source='product.price')
    total_price = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()  # Add method field for primary image

    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'product_title', 'product_slug', 'price', 'quantity', 'total_price', 'product_image', 'created_at', 'updated_at']
        read_only_fields = ['user']

    def get_total_price(self, obj):
        return obj.get_total_price()

    def get_product_image(self, obj):
        """Fetch the primary image URL for the product."""
        image = obj.product.thumbnail_image
        if image and hasattr(image, 'url'):
            return image.url
        return None

    