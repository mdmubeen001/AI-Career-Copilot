import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from resumes.models import Resume

from .models import InterviewAnswer, InterviewQuestion, InterviewSession
from .serializers import (
    InterviewAnswerSerializer,
    InterviewAnswerSubmitSerializer,
    InterviewQuestionSerializer,
    InterviewResultSerializer,
    InterviewSessionCreateSerializer,
    InterviewSessionListSerializer,
    InterviewSessionSerializer,
)
from .services.interview_agent import InterviewAgent

logger = logging.getLogger(__name__)


class InterviewSessionListCreateView(APIView):
    """
    GET: List all interview sessions for the authenticated user.
    POST: Create a new interview session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = InterviewSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = InterviewSessionListSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = InterviewSessionCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        resume_id = validated_data.get('resume_id')
        resume = None
        if resume_id:
            resume = Resume.objects.filter(id=resume_id, user=request.user).first()

        session = InterviewSession.objects.create(
            user=request.user,
            resume=resume,
            target_role=validated_data['target_role'],
            interview_type=validated_data.get('interview_type', 'mixed'),
            difficulty=validated_data.get('difficulty', 'intermediate'),
            total_questions=validated_data.get('total_questions', 5),
            current_question=0,
            status='not_started'
        )

        response_serializer = InterviewSessionSerializer(session)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class InterviewSessionDetailView(APIView):
    """
    GET: Retrieve details of an interview session belonging to the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        session = get_object_or_404(InterviewSession, id=pk, user=request.user)
        serializer = InterviewSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InterviewSessionStartView(APIView):
    """
    POST: Start the interview session, generate questions via InterviewAgent if needed,
          and transition status to 'in_progress'.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = get_object_or_404(InterviewSession, id=pk, user=request.user)

        if session.status == 'completed':
            return Response(
                {"detail": "This interview session is already completed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate questions if not already generated
        if not session.questions.exists():
            agent = InterviewAgent()
            generated = agent.generate_questions(
                target_role=session.target_role,
                interview_type=session.interview_type,
                difficulty=session.difficulty,
                total_questions=session.total_questions,
                user=request.user,
                resume=session.resume
            )

            with transaction.atomic():
                questions_to_create = [
                    InterviewQuestion(
                        session=session,
                        question_number=item['question_number'],
                        question_text=item['question_text'],
                        question_type=item['question_type'],
                        expected_topics=item.get('expected_topics', [])
                    )
                    for item in generated
                ]
                InterviewQuestion.objects.bulk_create(questions_to_create)

        # Transition status and update current question
        if session.status == 'not_started':
            session.status = 'in_progress'

        # Find first unanswered question number
        first_unanswered = (
            session.questions.filter(answer__isnull=True)
            .order_by('question_number')
            .first()
        )
        if first_unanswered:
            session.current_question = first_unanswered.question_number
        else:
            session.current_question = 1

        session.save()

        serializer = InterviewSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InterviewQuestionListView(APIView):
    """
    GET: Return questions for the specified session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        session = get_object_or_404(InterviewSession, id=pk, user=request.user)
        questions = session.questions.all().order_by('question_number')
        serializer = InterviewQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InterviewAnswerSubmitView(APIView):
    """
    POST: Submit an answer to a question in an active interview session.
    Evaluates answer via InterviewAgent, persists evaluation, and advances session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, question_id):
        session = get_object_or_404(InterviewSession, id=pk, user=request.user)

        if session.status == 'completed':
            return Response(
                {"detail": "Cannot submit answers to an already completed interview session."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Question must belong to this session
        question = get_object_or_404(
            InterviewQuestion,
            id=question_id,
            session=session
        )

        serializer = InterviewAnswerSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        answer_text = serializer.validated_data['answer_text']

        # Evaluate answer via InterviewAgent
        agent = InterviewAgent()
        eval_result = agent.evaluate_answer(
            question_text=question.question_text,
            question_type=question.question_type,
            expected_topics=question.expected_topics,
            answer_text=answer_text,
            target_role=session.target_role,
            difficulty=session.difficulty
        )

        # Save or update answer
        with transaction.atomic():
            answer, _ = InterviewAnswer.objects.update_or_create(
                question=question,
                defaults={
                    'answer_text': answer_text,
                    'score': eval_result.get('score', 0),
                    'evaluation': eval_result.get('evaluation', ''),
                    'strengths': eval_result.get('strengths', []),
                    'weaknesses': eval_result.get('weaknesses', []),
                    'missing_points': eval_result.get('missing_points', []),
                    'improvement_suggestions': eval_result.get('improvement_suggestions', [])
                }
            )

            # Check next unanswered question
            next_unanswered = (
                session.questions.filter(
                    question_number__gt=question.question_number,
                    answer__isnull=True
                )
                .order_by('question_number')
                .first()
            )
            if next_unanswered:
                session.current_question = next_unanswered.question_number
            else:
                # If no higher unanswered question, find any remaining unanswered
                any_unanswered = (
                    session.questions.filter(answer__isnull=True)
                    .order_by('question_number')
                    .first()
                )
                if any_unanswered:
                    session.current_question = any_unanswered.question_number
                else:
                    session.current_question = session.total_questions

            session.save()

        answer_serializer = InterviewAnswerSerializer(answer)
        return Response({
            "message": "Answer evaluated successfully.",
            "answer": answer_serializer.data,
            "current_question": session.current_question,
            "session_status": session.status,
            "is_all_answered": not session.questions.filter(answer__isnull=True).exists()
        }, status=status.HTTP_200_OK)


class InterviewSessionCompleteView(APIView):
    """
    POST: Complete the interview session, calculate overall evaluation,
          store final score & feedback, and transition status to 'completed'.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = get_object_or_404(InterviewSession, id=pk, user=request.user)

        # Gather all answers data
        answers = InterviewAnswer.objects.filter(question__session=session).select_related('question')
        answers_data = [
            {
                "question_number": ans.question.question_number,
                "question_text": ans.question.question_text,
                "question_type": ans.question.question_type,
                "answer_text": ans.answer_text,
                "score": ans.score,
                "evaluation": ans.evaluation,
                "strengths": ans.strengths,
                "weaknesses": ans.weaknesses,
                "missing_points": ans.missing_points,
                "improvement_suggestions": ans.improvement_suggestions
            }
            for ans in answers
        ]

        session_data = {
            "target_role": session.target_role,
            "interview_type": session.interview_type,
            "difficulty": session.difficulty,
            "total_questions": session.total_questions
        }

        agent = InterviewAgent()
        final_eval = agent.evaluate_session(session_data, answers_data)

        session.overall_score = final_eval.get('overall_score', 0)
        session.overall_feedback = final_eval.get('overall_feedback', '')
        session.strengths = final_eval.get('strengths', [])
        session.weaknesses = final_eval.get('weaknesses', [])
        session.recommendations = final_eval.get('recommendations', [])
        session.status = 'completed'
        session.save()

        serializer = InterviewResultSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InterviewSessionResultView(APIView):
    """
    GET: Retrieve final evaluation results, feedback, and question-by-question breakdown.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        session = get_object_or_404(InterviewSession, id=pk, user=request.user)
        serializer = InterviewResultSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
