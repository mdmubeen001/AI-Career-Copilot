from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from resumes.models import Resume
from jobs.models import JobDescription, JobMatch
from jobs.services.job_matcher import JobMatcher

User = get_user_model()


class JobModuleTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='job_user1@example.com',
            password='TestPassword123!',
            username='job_user1'
        )
        self.user2 = User.objects.create_user(
            email='job_user2@example.com',
            password='TestPassword123!',
            username='job_user2'
        )

        # Pre-seed resume for user1
        self.resume1 = Resume.objects.create(
            user=self.user1,
            original_filename="user1_resume.pdf",
            extracted_text="Python Django Backend Developer with experience building REST APIs, PostgreSQL, and Docker.",
            file_type="pdf",
            file_size=1024
        )

        # Pre-seed resume for user2
        self.resume2 = Resume.objects.create(
            user=self.user2,
            original_filename="user2_resume.pdf",
            extracted_text="Frontend Developer skilled in React, CSS, and TypeScript.",
            file_type="pdf",
            file_size=1024
        )

        self.jobs_url = reverse('job-list-create')
        self.matches_url = reverse('job-match-list')

    def test_1_authenticated_user_can_create_job_description(self):
        """1. Authenticated user can create JobDescription."""
        self.client.force_authenticate(user=self.user1)
        payload = {
            "title": "Python Django Developer",
            "company": "Tech Corp",
            "description": "We are seeking an experienced Python Django developer to build resilient backend microservices.",
            "source_url": "https://example.com/jobs/python-dev"
        }
        response = self.client.post(self.jobs_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Python Django Developer")
        self.assertEqual(response.data['company'], "Tech Corp")
        self.assertTrue(JobDescription.objects.filter(user=self.user1, title="Python Django Developer").exists())

    def test_2_unauthenticated_user_cannot_create_job_description(self):
        """2. Unauthenticated user cannot create JobDescription."""
        payload = {
            "title": "Python Developer",
            "description": "We need an engineer to develop web applications."
        }
        response = self.client.post(self.jobs_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_3_user_can_only_list_their_own_jobs(self):
        """3. User can only list their own jobs."""
        JobDescription.objects.create(
            user=self.user1,
            title="User 1 Job",
            description="A job created specifically by user 1 for backend development."
        )
        JobDescription.objects.create(
            user=self.user2,
            title="User 2 Job",
            description="A job created specifically by user 2 for frontend development."
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.jobs_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "User 1 Job")

    def test_4_user_can_retrieve_their_own_job(self):
        """4. User can retrieve their own job."""
        job = JobDescription.objects.create(
            user=self.user1,
            title="Senior Backend Engineer",
            description="High scale distributed systems with Python, Postgres, and Docker."
        )
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('job-detail', kwargs={'pk': job.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Senior Backend Engineer")

    def test_5_user_cannot_retrieve_another_users_job(self):
        """5. User cannot retrieve another user's job (returns 404)."""
        job2 = JobDescription.objects.create(
            user=self.user2,
            title="Confidential Role",
            description="Job description belonging exclusively to user 2."
        )
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('job-detail', kwargs={'pk': job2.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_6_user_can_create_match_using_their_own_resume(self):
        """6. User can create a match using their own resume."""
        job = JobDescription.objects.create(
            user=self.user1,
            title="Python Django Backend Developer",
            company="Startup Inc",
            description="Looking for Python, Django, REST API, Docker, and PostgreSQL skills."
        )
        self.client.force_authenticate(user=self.user1)
        match_url = reverse('job-match-create', kwargs={'pk': job.id})
        response = self.client.post(match_url, {'resume_id': self.resume1.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertIn('match_score_estimate', data)
        self.assertGreaterEqual(data['match_score_estimate'], 0)
        self.assertLessEqual(data['match_score_estimate'], 100)
        self.assertTrue(len(data['matching_skills']) > 0)
        self.assertTrue(len(data['recommendations']) > 0)
        self.assertEqual(data['job_title'], job.title)

    def test_7_user_cannot_match_using_another_users_resume(self):
        """7. User cannot match using another user's resume."""
        job = JobDescription.objects.create(
            user=self.user1,
            title="Backend Engineer",
            description="Need Python and PostgreSQL developer."
        )
        self.client.force_authenticate(user=self.user1)
        match_url = reverse('job-match-create', kwargs={'pk': job.id})

        # Try to match with resume2 belonging to user2
        response = self.client.post(match_url, {'resume_id': self.resume2.id})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])

    def test_8_user_cannot_match_against_another_users_job(self):
        """8. User cannot match against another user's job."""
        job2 = JobDescription.objects.create(
            user=self.user2,
            title="User 2 Job",
            description="Python and Cloud Developer wanted."
        )
        self.client.force_authenticate(user=self.user1)
        match_url = reverse('job-match-create', kwargs={'pk': job2.id})
        response = self.client.post(match_url, {'resume_id': self.resume1.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_9_match_score_validation(self):
        """9. Match score validation (0 to 100)."""
        job = JobDescription.objects.create(
            user=self.user1,
            title="Backend Role",
            description="Python software engineering role."
        )
        # Valid score
        valid_match = JobMatch(
            user=self.user1,
            resume=self.resume1,
            job_description=job,
            match_score_estimate=85,
            summary="Great match."
        )
        valid_match.full_clean()
        valid_match.save()
        self.assertEqual(valid_match.match_score_estimate, 85)

        # Invalid score > 100
        invalid_match = JobMatch(
            user=self.user1,
            resume=self.resume1,
            job_description=job,
            match_score_estimate=150,
            summary="Invalid score."
        )
        with self.assertRaises(ValidationError):
            invalid_match.full_clean()

    def test_10_matching_response_is_stored(self):
        """10. Matching response is stored in database."""
        job = JobDescription.objects.create(
            user=self.user1,
            title="Django Specialist",
            description="Building robust web applications with Django and REST Framework."
        )
        self.client.force_authenticate(user=self.user1)
        match_url = reverse('job-match-create', kwargs={'pk': job.id})
        response = self.client.post(match_url, {'resume_id': self.resume1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        match_id = response.data['id']
        stored = JobMatch.objects.filter(id=match_id, user=self.user1).first()
        self.assertIsNotNone(stored)
        self.assertEqual(stored.job_description, job)
        self.assertEqual(stored.resume, self.resume1)
        self.assertEqual(stored.match_score_estimate, response.data['match_score_estimate'])

    def test_11_match_history_returns_only_current_users_matches(self):
        """11. Match history returns only current user's matches."""
        job1 = JobDescription.objects.create(
            user=self.user1,
            title="User 1 Job",
            description="Python software developer description."
        )
        job2 = JobDescription.objects.create(
            user=self.user2,
            title="User 2 Job",
            description="Frontend developer description."
        )
        JobMatch.objects.create(
            user=self.user1,
            resume=self.resume1,
            job_description=job1,
            match_score_estimate=80,
            summary="User 1 match."
        )
        JobMatch.objects.create(
            user=self.user2,
            resume=self.resume2,
            job_description=job2,
            match_score_estimate=90,
            summary="User 2 match."
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.matches_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['job_title'], "User 1 Job")

    def test_12_malformed_empty_job_description_validation(self):
        """12. Malformed/empty job description validation."""
        self.client.force_authenticate(user=self.user1)

        # Empty title
        resp1 = self.client.post(self.jobs_url, {
            "title": "",
            "description": "Valid description with sufficient length for testing."
        })
        self.assertEqual(resp1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', resp1.data)

        # Too short description (<20 chars)
        resp2 = self.client.post(self.jobs_url, {
            "title": "Valid Title",
            "description": "Too short"
        })
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', resp2.data)

    def test_13_fallback_ai_mode_works_without_api_key(self):
        """13. Fallback AI mode works deterministically without API key."""
        job = JobDescription.objects.create(
            user=self.user1,
            title="Python Django Cloud Engineer",
            description="We are looking for Python, Django, PostgreSQL, Docker, AWS, and Git."
        )
        matcher = JobMatcher()
        result = matcher.match(resume=self.resume1, job_description=job, user=self.user1)

        self.assertIsInstance(result, dict)
        self.assertIn('match_score_estimate', result)
        self.assertGreaterEqual(result['match_score_estimate'], 40)
        self.assertLessEqual(result['match_score_estimate'], 100)
        self.assertIn('Python', result['matching_skills'])
        self.assertIn('Django', result['matching_skills'])
        self.assertTrue(len(result['recommendations']) > 0)
