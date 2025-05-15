# ecommerce/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Order endpoints
    path('', views.OrderListAPIView.as_view(), name='order-list'),
    path('<int:pk>/', views.OrderDetailAPIView.as_view(), name='order-detail'),
    path('create-order/', views.OrderCreateAPIView.as_view(), name='create-order'),
]