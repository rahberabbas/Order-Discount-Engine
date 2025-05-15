from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from discounts.models import DiscountRule
from .serializers import (
    DiscountRuleSerializer
)
from discounts.cache import invalidate_discount_rules_cache
import logging

logger = logging.getLogger(__name__)

# Create your views here.
class DiscountRuleListAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Retrieve all discount rules."""
        try:
            discount_rules = DiscountRule.objects.all()
            serializer = DiscountRuleSerializer(discount_rules, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving discount rules: {e}")
            return Response({"error": "An error occurred while fetching discount rules."}, status=500)
    
    def post(self, request):
        """Create a new discount rule."""
        try:
            serializer = DiscountRuleSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                invalidate_discount_rules_cache()
                logger.info(f"Discount rule created successfully.")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating discount rule: {e}")
            return Response({"error": "An error occurred while creating the discount rule."}, status=500)


class DiscountRuleDetailAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, pk):
        """Retrieve a single discount rule."""
        try:
            discount_rule = get_object_or_404(DiscountRule, pk=pk)
            serializer = DiscountRuleSerializer(discount_rule)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving discount rule {pk}: {e}")
            return Response({"error": "An error occurred while fetching the discount rule."}, status=500)
    
    def put(self, request, pk):
        """Update a discount rule."""
        try:
            discount_rule = get_object_or_404(DiscountRule, pk=pk)
            serializer = DiscountRuleSerializer(discount_rule, data=request.data)
            if serializer.is_valid():
                serializer.save()
                invalidate_discount_rules_cache()
                logger.info(f"Discount rule {pk} updated successfully.")
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating discount rule {pk}: {e}")
            return Response({"error": "An error occurred while updating the discount rule."}, status=500)
    
    def delete(self, request, pk):
        """Delete a discount rule."""
        try:
            discount_rule = get_object_or_404(DiscountRule, pk=pk)
            discount_rule.delete()
            invalidate_discount_rules_cache()
            logger.info(f"Discount rule {pk} deleted successfully.")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting discount rule {pk}: {e}")
            return Response({"error": "An error occurred while deleting the discount rule."}, status=500)