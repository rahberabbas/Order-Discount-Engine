from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from discounts.engine import DiscountEngine
from .serializers import CartSerializer
from django.shortcuts import get_object_or_404
from decimal import Decimal
from rest_framework.throttling import ScopedRateThrottle
from .models import *

import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Cart, Product
from .serializers import CartSerializer

logger = logging.getLogger(__name__)

class CartListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def _get_cart_items(self, user):
        """Get cart items for the user."""
        try:
            return Cart.objects.filter(user=user).order_by('created_at')
        except Exception as e:
            logger.error(f"Error fetching cart items for user {user.id}: {e}")
            raise Exception("Error fetching cart items.")
    
    def _calculate_totals(self, cart_items, discounted_result):
        """Calculate original, discount, and final totals."""
        original_total = sum(item.product.price * item.quantity for item in cart_items)
        total_discount = sum(d['amount'] for d in discounted_result['applied_discounts'])
        discounted_total = original_total - total_discount
        return original_total, total_discount, discounted_total

    def _validate_product(self, product_info_id: int, quantity: int) -> tuple[Product, bool, str]:
        """Validate product info and quantity."""
        try:
            product = Product.objects.get(id=product_info_id)
        except Product.DoesNotExist:
            logger.warning(f"Product with id {product_info_id} not found.")
            return None, False, "Product info does not exist."

        if not product.is_active:
            logger.warning(f"Product with id {product_info_id} is no longer active.")
            return product, False, "The selected product is no longer available."

        if product.stock_quantity and int(product.stock_quantity) < quantity:
            logger.warning(f"Not enough stock for product {product_info_id}. Only {product.stock_quantity} available.")
            return product, False, f"Only {product.stock_quantity} items left in stock."

        return product, True, ""

    def _get_or_create_cart_item(self, user, product: Product, data: dict) -> tuple[Cart, bool]:
        """Get existing cart item or create a new one."""
        cart_item = Cart.objects.filter(user=user, product=product).first()
        if cart_item:
            logger.info(f"Cart item found for product {product.id} for user {user.id}.")
        else:
            logger.info(f"Creating new cart item for product {product.id} for user {user.id}.")
        return cart_item, cart_item is not None

    def _send_response(self, data: dict, status_code: int):
        """Helper to send standardized response."""
        return Response(data, status=status_code)
    
    def get(self, request):
        """Get cart items with calculated prices and discounts."""
        try:
            cart_items = self._get_cart_items(request.user)

            # Initialize and run discount engine
            discount_engine = DiscountEngine(None, request.user)
            discount_engine.cart_items = cart_items
            discounted_result = discount_engine.get_cart_discounts()

            # Calculate totals
            original_total, total_discount, discounted_total = self._calculate_totals(cart_items, discounted_result)

            # Serialize cart items
            serializer = CartSerializer(cart_items, many=True)

            return self._send_response({
                "cart_items": serializer.data,
                "total_quantity": sum(item.quantity for item in cart_items),
                "original_price": str(original_total),
                "total_discount": str(total_discount),
                "discounted_price": str(discounted_total),
                "applied_discounts": discounted_result['applied_discounts']
            }, status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching cart items: {e}")
            return self._send_response({"error": "Internal server error."}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Add item to cart."""
        data = request.data.copy()
        data['user'] = request.user.id

        product_id = data.get('product')
        quantity = int(data.get('quantity', 1))

        if not product_id or not quantity:
            logger.warning("Missing product info or quantity in request.")
            return self._send_response({"error": "Product info and quantity are required."}, status.HTTP_400_BAD_REQUEST)

        # Validate product info and quantity
        product, is_valid, error = self._validate_product(product_id, quantity)
        if not is_valid:
            return self._send_response({"error": error}, status.HTTP_400_BAD_REQUEST)

        # Get or create cart item
        cart_item, exists = self._get_or_create_cart_item(request.user, product, data)

        try:
            if exists:
                # Update existing cart item
                cart_item.quantity += quantity
                cart_item.save()
                logger.info(f"Updated cart item for product {product.id} for user {request.user.id}.")
                return self._send_response(CartSerializer(cart_item).data, status.HTTP_200_OK)

            # Create new cart item
            serializer = CartSerializer(data=data)
            if serializer.is_valid():
                cart_item = serializer.save(user=request.user)
                logger.info(f"Created new cart item for product {product.id} for user {request.user.id}.")
                return self._send_response(CartSerializer(cart_item).data, status.HTTP_201_CREATED)

            logger.error(f"Cart item creation failed: {serializer.errors}")
            return self._send_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error processing cart item: {e}")
            return self._send_response({"error": "Internal server error."}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    
class CartDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def _get_cart(self, user, pk):
        """Get the cart item for the user or raise 404 if not found."""
        try:
            return get_object_or_404(Cart, pk=pk, user=user)
        except Exception as e:
            logger.error(f"Error fetching cart item with ID {pk} for user {user.id}: {e}")
            raise

    def _validate_product_availability(self, product, quantity):
        """Check if the product is available and if the quantity is valid."""
        if not product.is_active:
            logger.warning(f"Product {product.id} is no longer available.")
            return {"error": "The selected product is no longer available."}, status.HTTP_400_BAD_REQUEST

        if product.stock_quantity and int(product.stock_quantity) < quantity:
            logger.warning(f"Insufficient stock for product {product.id}. Only {product.stock_quantity} available.")
            return {"error": f"Only {product.stock_quantity} items left in stock."}, status.HTTP_400_BAD_REQUEST
        
        return None, None

    def get(self, request, pk):
        """Retrieve a cart item."""
        cart = self._get_cart(request.user, pk)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update a cart item."""
        cart = self._get_cart(request.user, pk)
        data = request.data
        serializer = CartSerializer(cart, data=data, partial=True)

        if serializer.is_valid():
            # Handle product and quantity validation
            if 'product' in serializer.validated_data:
                product = Product.objects.get(id=serializer.validated_data['product'].id)
                
                validation_error, status_code = self._validate_product_availability(product, serializer.validated_data['quantity'] if 'quantity' in serializer.validated_data else 0)
                if validation_error:
                    return Response(validation_error, status=status_code)

            elif 'quantity' in serializer.validated_data:
                product = cart.product
                validation_error, status_code = self._validate_product_availability(product, serializer.validated_data['quantity'])
                if validation_error:
                    return Response(validation_error, status=status_code)

            # Save the updated cart item
            serializer.save()
            logger.info(f"Cart item {cart.id} updated successfully for user {request.user.id}.")
            return Response(serializer.data)

        logger.error(f"Failed to update cart item {cart.id} for user {request.user.id}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete a cart item."""
        cart = self._get_cart(request.user, pk)
        cart.delete()
        logger.info(f"Cart item {cart.id} deleted successfully for user {request.user.id}.")
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemQuantityAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def _get_cart_and_product(self, user, pk):
        """Helper to fetch cart and product."""
        cart = get_object_or_404(Cart, pk=pk, user=user)
        product = cart.product
        return cart, product

    def _check_product_availability(self, product, quantity):
        """Check if the product is available and stock is sufficient."""
        if not product.is_active:
            logger.warning(f"Product {product.id} is no longer available.")
            return {"error": "The selected product is no longer available."}, status.HTTP_400_BAD_REQUEST

        if product.stock_quantity and int(product.stock_quantity) < quantity:
            logger.warning(f"Insufficient stock for product {product.id}. Requested quantity {quantity}, available {product.stock_quantity}.")
            return {"error": f"Only {product.stock_quantity} items left in stock."}, status.HTTP_400_BAD_REQUEST

        return None, None

class IncreaseCartItemQuantityAPIView(CartItemQuantityAPIView):
    """Increase cart item quantity by 1."""

    def post(self, request, pk):
        """Increase the cart item quantity."""
        cart, product = self._get_cart_and_product(request.user, pk)

        # Check if product is available and sufficient stock is present
        validation_error, status_code = self._check_product_availability(product, cart.quantity + 1)
        if validation_error:
            return Response(validation_error, status=status_code)

        # Increase the quantity by 1
        cart.quantity += 1
        cart.save()

        logger.info(f"Cart item {cart.id} quantity increased for user {request.user.id}. New quantity: {cart.quantity}")
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class DecreaseCartItemQuantityAPIView(CartItemQuantityAPIView):
    """Decrease cart item quantity by 1."""

    throttle_classes = ['ScopedRateThrottle']
    throttle_scope = 'cart_desc'
    
    def post(self, request, pk):
        """Decrease the cart item quantity."""
        cart, product = self._get_cart_and_product(request.user, pk)

        # Check if product is available
        validation_error, status_code = self._check_product_availability(product, cart.quantity - 1)
        if validation_error:
            return Response(validation_error, status=status_code)

        # Decrease the quantity by 1 or delete the cart item if quantity reaches 0
        if cart.quantity > 1:
            cart.quantity -= 1
            cart.save()
            logger.info(f"Cart item {cart.id} quantity decreased for user {request.user.id}. New quantity: {cart.quantity}")
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        else:
            cart.delete()
            logger.info(f"Cart item {cart.id} deleted for user {request.user.id}.")
            return Response(
                {"message": "Cart item deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )