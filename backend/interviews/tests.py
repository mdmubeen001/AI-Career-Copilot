from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from interviews.models import InterviewAnswer, InterviewQuestion, InterviewSession
from interviews.services.interview_agent import InterviewAgent
from resumes.models import Resume

User = get_user_model()


class InterviewModuleTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='interview_user1@example.com',
            password='TestPassword123!',
            username='interview_user1'
        )
        self.user2 = User.objects.create_user(
            email='interview_user2@example.com',
            password='TestPassword123!',
            username='interview_user2'
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

        self.list_create_url = reverse('interview-list-create')

    def test_1_authenticated_user_can_create_interview(self):
        """1. Authenticated user can create an interview session."""
        self.client.force_authenticate(user=self.user1)
        payload = {
            "resume_id": self.resume1.id,
            "target_role": "Python Django Developer",
            "interview_type": "mixed",
            "difficulty": "intermediate",
            "total_questions": 5
        }
        response = self.client.post(self.list_create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['target_role'], "Python Django Developer")
        self.assertEqual(response.data['interview_type'], "mixed")
        self.assertEqual(response.data['difficulty'], "intermediate")
        self.assertEqual(response.data['total_questions'], 5)
        self.assertEqual(response.data['status'], "not_started")
        self.assertTrue(InterviewSession.objects.filter(user=self.user1, target_role="Python Django Developer").exists())

    def test_2_unauthenticated_user_cannot_create_interview(self):
        """2. Unauthenticated user cannot create an interview session."""
        payload = {
            "target_role": "Python Developer",
            "interview_type": "technical",
            "difficulty": "intermediate",
            "total_questions": 5
        }
        response = self.client.post(self.list_create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_3_user_sees_only_own_sessions(self):
        """3. User sees only their own interview sessions in list view."""
        InterviewSession.objects.create(
            user=self.user1,
            target_role="Backend Developer",
            interview_type="technical",
            difficulty="beginner"
        )
        InterviewSession.objects.create(
            user=self.user2,
            target_role="Frontend Engineer",
            interview_type="behavioral",
            difficulty="advanced"
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['target_role'], "Backend Developer")

    def test_4_user_cannot_access_another_users_session(self):
        """4. User cannot access another user's session details."""
        session_user2 = InterviewSession.objects.create(
            user=self.user2,
            target_role="Data Scientist",
            interview_type="mixed",
            difficulty="intermediate"
        )

        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('interview-detail', kwargs={'pk': session_user2.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_5_user_cannot_use_another_users_resume(self):
        """5. User cannot create a session with another user's resume."""
        self.client.force_authenticate(user=self.user1)
        payload = {
            "resume_id": self.resume2.id,  # belongs to user2
            "target_role": "Full Stack Developer",
            "interview_type": "mixed",
            "difficulty": "intermediate",
            "total_questions": 5
        }
        response = self.client.post(self.list_create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("resume_id", response.data)

    def test_6_start_interview_generates_questions(self):
        """6. Start interview generates questions appropriate for the session."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Python Django Developer",
            interview_type="technical",
            difficulty="intermediate",
            total_questions=3
        )
        self.client.force_authenticate(user=self.user1)
        start_url = reverse('interview-start', kwargs={'pk': session.id})
        response = self.client.post(start_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(session.questions.count(), 3)
        self.assertEqual(len(response.data['questions']), 3)

    def test_7_session_status_changes_to_in_progress(self):
        """7. Starting an interview transitions its status to in_progress."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Software Engineer",
            interview_type="mixed",
            difficulty="beginner",
            total_questions=3
        )
        self.client.force_authenticate(user=self.user1)
        start_url = reverse('interview-start', kwargs={'pk': session.id})
        response = self.client.post(start_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, "in_progress")
        self.assertEqual(session.current_question, 1)

    def test_8_question_belongs_to_correct_session(self):
        """8. Generated questions strictly belong to the correct session."""
        session1 = InterviewSession.objects.create(
            user=self.user1,
            target_role="DevOps Engineer",
            total_questions=2
        )
        session2 = InterviewSession.objects.create(
            user=self.user1,
            target_role="QA Engineer",
            total_questions=2
        )
        self.client.force_authenticate(user=self.user1)
        self.client.post(reverse('interview-start', kwargs={'pk': session1.id}))
        self.client.post(reverse('interview-start', kwargs={'pk': session2.id}))

        q1_ids = set(session1.questions.values_list('id', flat=True))
        q2_ids = set(session2.questions.values_list('id', flat=True))
        self.assertTrue(q1_ids.isdisjoint(q2_ids))

    def test_9_answer_can_be_submitted(self):
        """9. Answer can be submitted to an active session question."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Python Django Developer",
            total_questions=2,
            status="in_progress",
            current_question=1
        )
        question = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            question_text="How do select_related and prefetch_related optimize queries?",
            question_type="technical",
            expected_topics=["select_related", "prefetch_related", "ORM"]
        )

        self.client.force_authenticate(user=self.user1)
        answer_url = reverse('interview-answer-submit', kwargs={
            'pk': session.id,
            'question_id': question.id
        })
        payload = {
            "answer_text": "select_related performs an SQL JOIN for single-valued relationships (ForeignKey, OneToOne), while prefetch_related executes a separate query with an IN lookup for many-to-many or reverse foreign keys."
        }
        response = self.client.post(answer_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("answer", response.data)
        self.assertTrue(InterviewAnswer.objects.filter(question=question).exists())

    def test_10_answer_evaluation_is_stored(self):
        """10. Answer evaluation is stored with score, strengths, weaknesses, and improvement suggestions."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Python Django Developer",
            total_questions=1,
            status="in_progress",
            current_question=1
        )
        question = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            question_text="Explain Django authentication and middleware.",
            question_type="technical",
            expected_topics=["authentication", "middleware"]
        )

        self.client.force_authenticate(user=self.user1)
        answer_url = reverse('interview-answer-submit', kwargs={
            'pk': session.id,
            'question_id': question.id
        })
        payload = {
            "answer_text": "Django middleware intercepts requests and responses globally. Authentication middleware associates the user with the request via session or JWT tokens."
        }
        response = self.client.post(answer_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ans = InterviewAnswer.objects.get(question=question)
        self.assertIsNotNone(ans.score)
        self.assertTrue(0 <= ans.score <= 100)
        self.assertTrue(len(ans.evaluation) > 0)
        self.assertIsInstance(ans.strengths, list)
        self.assertIsInstance(ans.weaknesses, list)
        self.assertIsInstance(ans.missing_points, list)
        self.assertIsInstance(ans.improvement_suggestions, list)

    def test_11_score_validation_0_to_100(self):
        """11. Score must be between 0 and 100."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Tester",
            total_questions=1
        )
        question = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            question_text="Sample question",
            question_type="technical"
        )
        ans = InterviewAnswer(
            question=question,
            answer_text="Sample answer",
            score=150
        )
        with self.assertRaises(ValidationError):
            ans.full_clean()

        ans.score = -10
        with self.assertRaises(ValidationError):
            ans.full_clean()

    def test_12_empty_answer_rejected(self):
        """12. Empty answer is rejected with validation error."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Python Developer",
            total_questions=1,
            status="in_progress"
        )
        question = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            question_text="What is a generator in Python?",
            question_type="technical"
        )
        self.client.force_authenticate(user=self.user1)
        answer_url = reverse('interview-answer-submit', kwargs={
            'pk': session.id,
            'question_id': question.id
        })
        response = self.client.post(answer_url, {"answer_text": "   "})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("answer_text", response.data)

    def test_13_another_users_question_cannot_be_answered(self):
        """13. A user cannot answer a question belonging to another user's session."""
        session_user2 = InterviewSession.objects.create(
            user=self.user2,
            target_role="React Developer",
            total_questions=1,
            status="in_progress"
        )
        question_user2 = InterviewQuestion.objects.create(
            session=session_user2,
            question_number=1,
            question_text="What are React hooks?",
            question_type="technical"
        )
        self.client.force_authenticate(user=self.user1)
        answer_url = reverse('interview-answer-submit', kwargs={
            'pk': session_user2.id,
            'question_id': question_user2.id
        })
        response = self.client.post(answer_url, {"answer_text": "Hooks allow function components to use state."})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_14_completed_interview_cannot_be_answered_again(self):
        """14. Completed interview cannot accept new answers."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Security Engineer",
            total_questions=1,
            status="completed"
        )
        question = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            question_text="Describe CSRF attacks and defenses.",
            question_type="technical"
        )
        self.client.force_authenticate(user=self.user1)
        answer_url = reverse('interview-answer-submit', kwargs={
            'pk': session.id,
            'question_id': question.id
        })
        response = self.client.post(answer_url, {"answer_text": "CSRF tokens validate origin."})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("completed", response.data.get("detail", "").lower())

    def test_15_final_evaluation_is_stored(self):
        """15. Completing an interview stores overall score, feedback, and recommendations."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Python Django Developer",
            interview_type="mixed",
            difficulty="intermediate",
            total_questions=1,
            status="in_progress"
        )
        question = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            question_text="How do you structure Django apps for maintainability?",
            question_type="technical",
            expected_topics=["architecture", "services"]
        )
        InterviewAnswer.objects.create(
            question=question,
            answer_text="By separating business logic into services and keeping models and views lean.",
            score=85,
            evaluation="Strong architectural perspective.",
            strengths=["Clean separation of concerns"],
            weaknesses=["Could mention domain-driven design"],
            missing_points=["Data validation layers"],
            improvement_suggestions=["Expand on service layer patterns"]
        )

        self.client.force_authenticate(user=self.user1)
        complete_url = reverse('interview-complete', kwargs={'pk': session.id})
        response = self.client.post(complete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        session.refresh_from_db()
        self.assertEqual(session.status, "completed")
        self.assertEqual(session.overall_score, 85)
        self.assertTrue(len(session.overall_feedback) > 0)
        self.assertTrue(len(session.strengths) > 0)
        self.assertTrue(len(session.recommendations) > 0)

    def test_16_result_endpoint_returns_correct_data(self):
        """16. Result endpoint returns overall evaluation and question breakdown."""
        session = InterviewSession.objects.create(
            user=self.user1,
            target_role="Frontend Engineer",
            interview_type="technical",
            difficulty="intermediate",
            total_questions=1,
            status="completed",
            overall_score=88,
            overall_feedback="Excellent interview performance."
        )
        question = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            question_text="Explain useMemo vs useCallback.",
            question_type="technical"
        )
        InterviewAnswer.objects.create(
            question=question,
            answer_text="useMemo caches computed values, useCallback caches function references.",
            score=88,
            evaluation="Precise distinction."
        )

        self.client.force_authenticate(user=self.user1)
        result_url = reverse('interview-result', kwargs={'pk': session.id})
        response = self.client.get(result_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['overall_score'], 88)
        self.assertEqual(response.data['overall_feedback'], "Excellent interview performance.")
        self.assertEqual(len(response.data['questions']), 1)
        self.assertEqual(response.data['questions'][0]['answer']['score'], 88)

    def test_17_fallback_ai_mode_works_without_api_key(self):
        """17. Fallback AI mode deterministically generates questions, evaluates answers, and synthesizes sessions."""
        agent = InterviewAgent()

        # 1. Question generation fallback
        questions = agent.generate_questions(
            target_role="Python Django Developer",
            interview_type="mixed",
            difficulty="intermediate",
            total_questions=3
        )
        self.assertEqual(len(questions), 3)
        self.assertEqual(questions[0]['question_number'], 1)
        self.assertIn("question_text", questions[0])
        self.assertIn("expected_topics", questions[0])

        # 2. Answer evaluation fallback
        eval_result = agent.evaluate_answer(
            question_text=questions[0]['question_text'],
            question_type=questions[0]['question_type'],
            expected_topics=questions[0]['expected_topics'],
            answer_text="We use select_related for single relationships and prefetch_related for many relationships to avoid N+1 queries.",
            target_role="Python Django Developer"
        )
        self.assertIn("score", eval_result)
        self.assertTrue(0 <= eval_result['score'] <= 100)
        self.assertIn("evaluation", eval_result)
        self.assertTrue(len(eval_result['strengths']) > 0)
        self.assertTrue(len(eval_result['improvement_suggestions']) > 0)

        # 3. Session evaluation fallback
        session_data = {
            "target_role": "Python Django Developer",
            "interview_type": "mixed",
            "difficulty": "intermediate",
            "total_questions": 1
        }
        answers_data = [
            {
                "question_number": 1,
                "question_text": questions[0]['question_text'],
                "score": eval_result['score'],
                "strengths": eval_result['strengths'],
                "weaknesses": eval_result['weaknesses']
            }
        ]
        session_eval = agent.evaluate_session(session_data, answers_data)
        self.assertIn("overall_score", session_eval)
        self.assertEqual(session_eval['overall_score'], eval_result['score'])
        self.assertTrue(len(session_eval['overall_feedback']) > 0)
        self.assertTrue(len(session_eval['recommendations']) > 0)
