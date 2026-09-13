from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Profile

User = get_user_model()


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('accounts:auth-register')
        self.login_url = reverse('accounts:auth-login')
        self.refresh_url = reverse('accounts:auth-refresh')
        self.profile_url = reverse('accounts:user-profile')

        self.user_data = {
            'email': 'student@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'full_name': 'Alex Student',
        }

    def test_register_success_with_tokens(self):
        """User can register and receive JWT access & refresh tokens immediately."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['email'], 'student@example.com')
        self.assertEqual(response.data['user']['full_name'], 'Alex Student')

        # Check database records
        user = User.objects.get(email='student@example.com')
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('StrongPassword123!'))
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.full_name, 'Alex Student')

    def test_register_without_optional_fields(self):
        """Username and full_name are optional during registration."""
        payload = {
            'email': 'minimal@example.com',
            'password': 'StrongPassword123!',
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='minimal@example.com')
        self.assertIsNone(user.username)
        self.assertEqual(user.profile.full_name, '')

    def test_register_duplicate_email_fails(self):
        """Registering with an existing email returns 400 with a clear error."""
        User.objects.create_user(email='existing@example.com', password='Password123!')
        payload = {
            'email': 'existing@example.com',
            'password': 'StrongPassword123!',
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_password_mismatch_fails(self):
        """Mismatched passwords return 400 error."""
        payload = {
            'email': 'mismatch@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'DifferentPassword123!',
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_register_short_password_fails(self):
        """Passwords shorter than 8 characters fail validation."""
        payload = {
            'email': 'short@example.com',
            'password': 'short',
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_success(self):
        """User can log in using email and password to receive tokens."""
        user = User.objects.create_user(
            email='login@example.com',
            password='StrongPassword123!',
        )
        user.profile.full_name = 'Login User'
        user.profile.save()

        payload = {
            'email': 'login@example.com',
            'password': 'StrongPassword123!',
        }
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'login@example.com')
        self.assertEqual(response.data['user']['full_name'], 'Login User')

    def test_login_invalid_credentials(self):
        """Invalid credentials return 401 Unauthorized."""
        User.objects.create_user(email='valid@example.com', password='StrongPassword123!')
        payload = {
            'email': 'valid@example.com',
            'password': 'WrongPassword123!',
        }
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Valid refresh token can generate a new access token."""
        User.objects.create_user(email='refresh@example.com', password='StrongPassword123!')
        login_resp = self.client.post(
            self.login_url,
            {'email': 'refresh@example.com', 'password': 'StrongPassword123!'},
        )
        refresh_token = login_resp.data['refresh']

        refresh_resp = self.client.post(self.refresh_url, {'refresh': refresh_token})
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_resp.data)


class ProfileTests(APITestCase):
    def setUp(self):
        self.profile_url = reverse('accounts:user-profile')
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='Password123!',
        )
        self.user1.profile.full_name = 'User One'
        self.user1.profile.save()

        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='Password123!',
        )
        self.user2.profile.full_name = 'User Two'
        self.user2.profile.save()

    def test_unauthenticated_profile_access_blocked(self):
        """Unauthenticated requests to /api/v1/profile/ receive 401."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_profile_retrieval(self):
        """User can retrieve their own profile."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user1@example.com')
        self.assertEqual(response.data['full_name'], 'User One')

    def test_profile_update(self):
        """User can update their own profile fields."""
        self.client.force_authenticate(user=self.user1)
        update_data = {
            'full_name': 'Alex Updated',
            'education': 'Undergraduate',
            'college': 'Stanford University',
            'degree': 'B.S. Computer Science',
            'graduation_year': 2026,
            'skills': ['Python', 'Django', 'React'],
            'interests': ['AI Agents', 'System Design'],
            'career_goal': 'AI Engineer',
        }
        response = self.client.put(self.profile_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['college'], 'Stanford University')
        self.assertEqual(response.data['graduation_year'], 2026)
        self.assertEqual(response.data['skills'], ['Python', 'Django', 'React'])
        self.assertEqual(response.data['career_goal'], 'AI Engineer')

        # Verify DB persistence
        self.user1.profile.refresh_from_db()
        self.assertEqual(self.user1.profile.graduation_year, 2026)
        self.assertEqual(self.user1.profile.skills, ['Python', 'Django', 'React'])

    def test_profile_comma_separated_skills_normalized(self):
        """Comma-separated skills and interests are cleanly normalized to lists."""
        self.client.force_authenticate(user=self.user1)
        update_data = {
            'skills': 'Python, Django, FastAPI',
            'interests': 'Cloud, DevOps',
        }
        response = self.client.patch(self.profile_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['skills'], ['Python', 'Django', 'FastAPI'])
        self.assertEqual(response.data['interests'], ['Cloud', 'DevOps'])

    def test_profile_invalid_graduation_year(self):
        """Invalid graduation year returns 400 validation error."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(self.profile_url, {'graduation_year': 1800}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('graduation_year', response.data)

    def test_profile_isolation(self):
        """Users can only access their own profile; User2 only sees User2 data."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user2@example.com')
        self.assertEqual(response.data['full_name'], 'User Two')
