from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Profile
from .serializers import (
    CustomTokenObtainPairSerializer,
    ProfileSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration using email and password.
    Returns the created user info along with JWT authentication tokens.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens for seamless first-time authentication
        refresh = RefreshToken.for_user(user)
        profile = Profile.objects.filter(user=user).first()

        response_data = {
            'message': 'User registered successfully.',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': profile.full_name if profile else '',
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API endpoint for user login. Authenticates with email and password,
    returning access/refresh tokens and basic user info.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """
    API endpoint to refresh an expired access token using a valid refresh token.
    """
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to retrieve and update the authenticated user's profile.
    Users can only view and modify their own profile.
    Supports GET, PUT, and PATCH.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile
