from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Profile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration using email and password.
    Username is optional and not required.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Must be at least 8 characters and pass password validation.',
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'},
        help_text='Optional password confirmation. If provided, must match password.',
    )
    full_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=255,
        help_text='Optional full name for the user profile.',
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'password_confirm', 'full_name']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    def validate_email(self, value):
        normalized_email = value.lower().strip()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError('A user with this email address already exists.')
        return normalized_email

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        # If confirmation is provided, verify match
        if password_confirm is not None and password_confirm != '' and password != password_confirm:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})

        # Validate password strength using Django's built-in validators
        temp_user = User(email=attrs.get('email', ''))
        try:
            validate_password(password=password, user=temp_user)
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        full_name = validated_data.pop('full_name', '')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        username = validated_data.pop('username', None)

        user = User.objects.create_user(
            email=email,
            password=password,
            username=username if username else None,
            **validated_data,
        )

        # Update profile full_name if provided
        if full_name:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.full_name = full_name
            profile.save(update_fields=['full_name'])
            user.profile = profile

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Token serializer authenticating via email.
    Returns access, refresh tokens and authenticated user metadata.
    """
    username_field = 'email'

    def validate(self, attrs):
        # Normalize email
        if 'email' in attrs:
            attrs['email'] = attrs['email'].lower().strip()

        data = super().validate(attrs)

        profile = getattr(self.user, 'profile', None)
        full_name = profile.full_name if profile else ''

        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'full_name': full_name,
        }
        return data


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating user profile information.
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'email',
            'full_name',
            'education',
            'college',
            'degree',
            'graduation_year',
            'skills',
            'interests',
            'career_goal',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']

    def validate_graduation_year(self, value):
        if value is not None:
            if value < 1950 or value > 2100:
                raise serializers.ValidationError('Graduation year must be between 1950 and 2100.')
        return value

    def validate_skills(self, value):
        if isinstance(value, str):
            # Parse comma-separated strings into a list
            return [item.strip() for item in value.split(',') if item.strip()]
        elif isinstance(value, list):
            # Clean list elements
            return [str(item).strip() for item in value if str(item).strip()]
        raise serializers.ValidationError('Skills must be a list of strings or a comma-separated string.')

    def validate_interests(self, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        elif isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise serializers.ValidationError('Interests must be a list of strings or a comma-separated string.')
