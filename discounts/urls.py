# ecommerce/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Discount rule endpoints (admin only)
    path('', views.DiscountRuleListAPIView.as_view(), name='discount-rule-list'),
    path('<int:pk>/', views.DiscountRuleDetailAPIView.as_view(), name='discount-rule-detail'),
]