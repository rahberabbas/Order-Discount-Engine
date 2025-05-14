# urls.py
from django.urls import path
from .views import CategoryListCreateAPIView, CategoryDetailAPIView, ProductListCreateAPIView, ProductRetrieveUpdateDeleteAPIView

urlpatterns = [
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryDetailAPIView.as_view(), name='category-detail'),
    
    path('', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('<str:slug>/', ProductRetrieveUpdateDeleteAPIView.as_view(), name='product-detail'),
]
