# serializers.py
from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# serializers.py
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from .models import Product, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    products_image = ProductImageSerializer(many=True, required=False)
    thumbnail_image = Base64ImageField(required=False)
    category = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price', 'category', 'stock_quantity',
                  'thumbnail_image', 'products_image', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        images_data = validated_data.pop('products_image', [])
        product = Product.objects.create(**validated_data)
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop('products_image', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if images_data is not None:
            instance.products_image.all().delete()  # Optional: remove old images
            for image_data in images_data:
                ProductImage.objects.create(product=instance, **image_data)

        return instance