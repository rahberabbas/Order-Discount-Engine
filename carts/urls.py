from django.urls import path
from .views import *

urlpatterns = [
    path('', CartListCreateAPIView.as_view(), name='cart-list-create'),
    path('<int:pk>/', CartDetailAPIView.as_view(), name='cart-detail'),
    path('<int:pk>/increase/', IncreaseCartItemQuantityAPIView.as_view(), name='cart-increase-quantity'),
    path('<int:pk>/decrease/', DecreaseCartItemQuantityAPIView.as_view(), name='cart-decrease-quantity'),
]
