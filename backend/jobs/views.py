from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from resumes.models import Resume
from .models import JobDescription, JobMatch
from .serializers import (
    JobDescriptionSerializer,
    JobMatchListSerializer,
    JobMatchRequestSerializer,
    JobMatchSerializer,
)
from .services.job_matcher import JobMatcher


class JobDescriptionListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list or create Job Descriptions for the authenticated user.
    GET /api/v1/jobs/
    POST /api/v1/jobs/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JobDescriptionSerializer

    def get_queryset(self):
        return JobDescription.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class JobDescriptionDetailView(generics.RetrieveDestroyAPIView):
    """
    API endpoint to retrieve or delete an authenticated user's Job Description.
    GET /api/v1/jobs/<id>/
    DELETE /api/v1/jobs/<id>/
    Returns 404 if the job description belongs to another user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JobDescriptionSerializer

    def get_queryset(self):
        return JobDescription.objects.filter(user=self.request.user)


class JobMatchCreateView(views.APIView):
    """
    API endpoint to evaluate a candidate Resume against a specific Job Description.
    POST /api/v1/jobs/<id>/match/
    Payload: {"resume_id": <int>}
    Strictly verifies ownership of both the Resume and the Job Description.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        # 1. Verify Job Description belongs to current user
        job_description = get_object_or_404(JobDescription, pk=pk, user=request.user)

        # 2. Validate incoming request and resume ownership
        req_serializer = JobMatchRequestSerializer(data=request.data, context={'request': request})
        req_serializer.is_valid(raise_exception=True)
        resume_id = req_serializer.validated_data['resume_id']

        resume = get_object_or_404(Resume, pk=resume_id, user=request.user)

        if not resume.extracted_text.strip():
            return Response(
                {"detail": "The selected resume contains no readable text. Please re-upload your resume."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Execute Job Matcher service
        matcher = JobMatcher()
        try:
            match_data = matcher.match(
                resume=resume,
                job_description=job_description,
                user=request.user
            )
        except Exception as exc:
            return Response(
                {"detail": f"Job matching evaluation failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4. Save JobMatch record
        match = JobMatch.objects.create(
            user=request.user,
            resume=resume,
            job_description=job_description,
            match_score_estimate=match_data.get('match_score_estimate', 0),
            summary=match_data.get('summary', ''),
            matching_skills=match_data.get('matching_skills', []),
            missing_skills=match_data.get('missing_skills', []),
            strengths=match_data.get('strengths', []),
            gaps=match_data.get('gaps', []),
            recommendations=match_data.get('recommendations', []),
        )

        resp_serializer = JobMatchSerializer(match)
        return Response(resp_serializer.data, status=status.HTTP_201_CREATED)


class JobMatchListView(generics.ListAPIView):
    """
    API endpoint to list historical Job Matches for the authenticated user.
    GET /api/v1/jobs/matches/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JobMatchListSerializer

    def get_queryset(self):
        return (
            JobMatch.objects.filter(user=self.request.user)
            .select_related('job_description', 'resume')
            .order_by('-created_at')
        )


class JobMatchDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve full details of an individual Job Match.
    GET /api/v1/jobs/matches/<id>/
    Returns 404 if the match belongs to another user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JobMatchSerializer

    def get_queryset(self):
        return (
            JobMatch.objects.filter(user=self.request.user)
            .select_related('job_description', 'resume')
        )
