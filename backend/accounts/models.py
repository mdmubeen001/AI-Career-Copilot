from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Custom User model where email is the unique identifier for authentication.
    Username is not required.
    """
    username = models.CharField(
        _('username'),
        max_length=150,
        blank=True,
        null=True,
        help_text=_('Optional. 150 characters or fewer.'),
    )
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Profile(models.Model):
    """
    User profile storing education, skills, interests, and career goals.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    full_name = models.CharField(max_length=255, blank=True, default='')
    education = models.CharField(max_length=255, blank=True, default='')
    college = models.CharField(max_length=255, blank=True, default='')
    degree = models.CharField(max_length=255, blank=True, default='')
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    career_goal = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"
