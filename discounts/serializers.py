from rest_framework import serializers
from .models import DiscountRule

class DiscountRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountRule
        fields = '__all__'