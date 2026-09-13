from django.urls import path

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    ProfileView,
    RegisterView,
)

app_name = 'accounts'

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='auth-refresh'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
]
