from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CareerProfile, Skill, UserSkill

User = get_user_model()


class CareerModuleTests(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='TestPassword123!',
            username='user1'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='TestPassword123!',
            username='user2'
        )

        # Pre-seed skills
        self.skill_python = Skill.objects.create(name='Python')
        self.skill_django = Skill.objects.create(name='Django')

        # Endpoints
        self.profile_url = reverse('career:career-profile')
        self.skills_url = reverse('career:skill-list-create')
        self.user_skills_url = reverse('career:user-skill-list-create')
        self.sync_skills_url = reverse('career:user-skill-sync')

    def test_unauthenticated_access_denied(self):
        """Verify all career endpoints require authentication."""
        resp1 = self.client.get(self.profile_url)
        self.assertEqual(resp1.status_code, status.HTTP_401_UNAUTHORIZED)

        resp2 = self.client.get(self.skills_url)
        self.assertEqual(resp2.status_code, status.HTTP_401_UNAUTHORIZED)

        resp3 = self.client.get(self.user_skills_url)
        self.assertEqual(resp3.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_career_profile_get_and_update(self):
        """User can retrieve and update their career profile."""
        self.client.force_authenticate(user=self.user1)

        # First GET creates default profile
        get_resp = self.client.get(self.profile_url)
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(get_resp.data['email'], 'user1@example.com')
        self.assertEqual(get_resp.data['target_role'], '')

        # Update profile
        update_data = {
            'current_role': 'Junior Python Developer',
            'target_role': 'Senior AI Engineer',
            'experience_level': 'Entry-level (0-2 years)',
            'bio': 'Passionate about autonomous agents and full-stack systems.'
        }
        put_resp = self.client.put(self.profile_url, update_data, format='json')
        self.assertEqual(put_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(put_resp.data['current_role'], 'Junior Python Developer')
        self.assertEqual(put_resp.data['target_role'], 'Senior AI Engineer')
        self.assertEqual(put_resp.data['experience_level'], 'Entry-level (0-2 years)')
        self.assertEqual(put_resp.data['bio'], 'Passionate about autonomous agents and full-stack systems.')

        # Verify in database
        profile = CareerProfile.objects.get(user=self.user1)
        self.assertEqual(profile.target_role, 'Senior AI Engineer')

    def test_available_skills_list_and_create(self):
        """Users can list skills and create new skills."""
        self.client.force_authenticate(user=self.user1)

        # List skills
        list_resp = self.client.get(self.skills_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        skill_names = [s['name'] for s in list_resp.data]
        self.assertIn('Python', skill_names)
        self.assertIn('Django', skill_names)

        # Search filter
        search_resp = self.client.get(self.skills_url, {'search': 'pyt'})
        self.assertEqual(len(search_resp.data), 1)
        self.assertEqual(search_resp.data[0]['name'], 'Python')

        # Create new skill
        create_resp = self.client.post(self.skills_url, {'name': 'React'}, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_resp.data['name'], 'React')

        # Create duplicate skill returns existing
        dup_resp = self.client.post(self.skills_url, {'name': 'react'}, format='json')
        self.assertEqual(dup_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(dup_resp.data['id'], create_resp.data['id'])

    def test_user_skills_crud_and_isolation(self):
        """User can add, update, list, and delete skills, strictly isolated from other users."""
        self.client.force_authenticate(user=self.user1)

        # Add skill by name
        add_resp = self.client.post(
            self.user_skills_url,
            {'name': 'FastAPI', 'level': 'Intermediate'},
            format='json'
        )
        self.assertEqual(add_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(add_resp.data['skill_name'], 'FastAPI')
        self.assertEqual(add_resp.data['level'], 'Intermediate')
        user1_skill_id = add_resp.data['id']

        # Add skill by ID
        add_resp2 = self.client.post(
            self.user_skills_url,
            {'skill_id': self.skill_python.id, 'level': 'Advanced'},
            format='json'
        )
        self.assertEqual(add_resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(add_resp2.data['skill_name'], 'Python')

        # List user skills
        user1_list = self.client.get(self.user_skills_url)
        self.assertEqual(len(user1_list.data), 2)

        # Authenticate as user2
        self.client.force_authenticate(user=self.user2)

        # User 2 list should be empty
        user2_list = self.client.get(self.user_skills_url)
        self.assertEqual(len(user2_list.data), 0)

        # User 2 cannot access or delete User 1's skill
        detail_url = reverse('career:user-skill-detail', kwargs={'pk': user1_skill_id})
        forbidden_get = self.client.get(detail_url)
        self.assertEqual(forbidden_get.status_code, status.HTTP_404_NOT_FOUND)

        forbidden_delete = self.client.delete(detail_url)
        self.assertEqual(forbidden_delete.status_code, status.HTTP_404_NOT_FOUND)

        # Switch back to user1 to verify skill still exists and delete it
        self.client.force_authenticate(user=self.user1)
        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deleted
        after_del = self.client.get(self.user_skills_url)
        self.assertEqual(len(after_del.data), 1)

    def test_user_skills_bulk_sync(self):
        """User can sync their skills list with mixed levels."""
        self.client.force_authenticate(user=self.user1)

        payload = {
            'skills': [
                {'name': 'Python', 'level': 'Advanced'},
                {'name': 'PostgreSQL', 'level': 'Intermediate'},
                'Docker'
            ]
        }
        sync_resp = self.client.post(self.sync_skills_url, payload, format='json')
        self.assertEqual(sync_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(sync_resp.data), 3)

        skills_dict = {item['skill_name']: item['level'] for item in sync_resp.data}
        self.assertEqual(skills_dict['Python'], 'Advanced')
        self.assertEqual(skills_dict['PostgreSQL'], 'Intermediate')
        self.assertEqual(skills_dict['Docker'], 'Beginner')
