# views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from rest_framework.permissions import IsAdminUser, AllowAny

# Configure logger
logger = logging.getLogger(__name__)

class CategoryListCreateAPIView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        try:
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return Response({'error': 'Failed to fetch categories.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = CategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Category created: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            logger.warning(f"Invalid data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            return Response({'error': 'Failed to create category.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryDetailAPIView(APIView):
    permission_classes = [IsAdminUser]
    def get_object(self, pk):
        try:
            return get_object_or_404(Category, pk=pk)
        except ObjectDoesNotExist:
            logger.warning(f"Category with ID {pk} not found.")
            return None

    def get(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def put(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            serializer = CategorySerializer(category, data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Category updated (ID {pk}): {serializer.data}")
                return Response(serializer.data)
            logger.warning(f"Invalid update data for ID {pk}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating category ID {pk}: {str(e)}")
            return Response({'error': 'Failed to update category.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            category.delete()
            logger.info(f"Category deleted (ID {pk})")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting category ID {pk}: {str(e)}")
            return Response({'error': 'Failed to delete category.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductListCreateAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]
    
    def get(self, request):
        try:
            products = Product.objects.all()
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return Response({'error': 'Failed to fetch products.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save()
                logger.info(f"Product created: {product}")
                return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
            logger.warning(f"Product creation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            return Response({'error': 'Failed to create product.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ProductRetrieveUpdateDeleteAPIView(APIView):
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def get_object(self, slug):
        return get_object_or_404(Product, slug=slug)

    def get(self, request, slug):
        try:
            product = self.get_object(slug)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving product {slug}: {str(e)}")
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, slug):
        try:
            product = self.get_object(slug)
            serializer = ProductSerializer(product, data=request.data)
            if serializer.is_valid():
                product = serializer.save()
                logger.info(f"Product {slug} fully updated.")
                return Response(ProductSerializer(product).data)
            logger.warning(f"Full update failed for product {slug}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating product {slug}: {str(e)}")
            return Response({'error': 'Failed to update product.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, slug):
        try:
            product = self.get_object(slug)
            serializer = ProductSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                product = serializer.save()
                logger.info(f"Product {slug} partially updated.")
                return Response(ProductSerializer(product).data)
            logger.warning(f"Partial update failed for product {slug}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error patching product {slug}: {str(e)}")
            return Response({'error': 'Failed to patch product.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, slug):
        try:
            product = self.get_object(slug)
            product.delete()
            logger.info(f"Product {slug} deleted.")
            return Response({'message': 'Product deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting product {slug}: {str(e)}")
            return Response({'error': 'Failed to delete product.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)