from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.utils import get_tokens_for_user
from .serializers import *
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

class RegisterView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning("Registration validation failed: %s", serializer.errors)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid data provided",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = serializer.save()
                token_data = get_tokens_for_user(user)

                logger.info("New user registered: %s", user.email)

                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "User created successfully",
                    "data": serializer.data,
                    "token": token_data['access'],
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("Error during user registration: %s", str(e), exc_info=True)
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Something went wrong while registering the user."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data

            logger.info(f"User logged in: {user.email}")

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Login successful',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data,
            }, status=status.HTTP_200_OK)

        logger.warning("Login failed with errors: %s", serializer.errors)
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'Invalid login credentials',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class TokenRefreshView(APIView):
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
