import os
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Resume, ResumeAnalysis
from .serializers import (
    ResumeAnalysisSerializer,
    ResumeAnalyzeRequestSerializer,
    ResumeDetailSerializer,
    ResumeListSerializer,
    ResumeUploadSerializer,
)
from .services.document_parser import DocumentParser
from .services.resume_analyzer import ResumeAnalyzer


class ResumeUploadView(views.APIView):
    """
    API endpoint to upload a resume file (PDF or DOCX).
    POST /api/v1/resumes/upload/
    Extracts text automatically using DocumentParser, creates a Resume record,
    and optionally executes initial analysis if requested or target_role is supplied.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = ResumeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']
        target_role = serializer.validated_data.get('target_role', '').strip()
        auto_analyze = request.data.get('auto_analyze', 'true').lower() in ('true', '1')

        # Extract text via DocumentParser
        try:
            extracted_text, file_type = DocumentParser.parse_file(uploaded_file)
        except ValueError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as exc:
            return Response(
                {'detail': f"Failed to parse resume document: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create resume instance for user
        resume = Resume.objects.create(
            user=request.user,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            extracted_text=extracted_text,
            file_type=file_type,
            file_size=uploaded_file.size
        )

        # Trigger automatic analysis if requested
        if auto_analyze or target_role:
            # Fallback target_role to user career profile if empty
            if not target_role:
                career_profile = getattr(request.user, 'career_profile', None)
                if career_profile and career_profile.target_role:
                    target_role = career_profile.target_role

            try:
                analyzer = ResumeAnalyzer()
                analysis_data = analyzer.analyze_resume(
                    resume_text=extracted_text,
                    target_role=target_role
                )
                ResumeAnalysis.objects.create(
                    resume=resume,
                    target_role=target_role,
                    summary=analysis_data.get('summary', ''),
                    ats_score_estimate=analysis_data.get('ats_score_estimate', 0),
                    detected_skills=analysis_data.get('detected_skills', []),
                    missing_skills=analysis_data.get('missing_skills', []),
                    strengths=analysis_data.get('strengths', []),
                    weaknesses=analysis_data.get('weaknesses', []),
                    experience_summary=analysis_data.get('experience_summary', ''),
                    education_summary=analysis_data.get('education_summary', ''),
                    project_summary=analysis_data.get('project_summary', ''),
                    recommendations=analysis_data.get('recommendations', [])
                )
            except Exception as e:
                # Log error and preserve uploaded resume
                print(f"[ResumeUploadView] Automatic analysis failed: {e}")

        # Refresh from db with analysis relation
        resume.refresh_from_db()
        detail_serializer = ResumeDetailSerializer(resume)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class ResumeListView(generics.ListAPIView):
    """
    API endpoint to list all resumes uploaded by the authenticated user.
    GET /api/v1/resumes/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResumeListSerializer

    def get_queryset(self):
        return (
            Resume.objects.filter(user=self.request.user)
            .select_related('analysis')
            .order_by('-uploaded_at')
        )


class ResumeDetailView(generics.RetrieveDestroyAPIView):
    """
    API endpoint to retrieve full details or delete an uploaded resume.
    GET /api/v1/resumes/<id>/
    DELETE /api/v1/resumes/<id>/
    Strictly isolated: returns 404 for resumes belonging to another user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResumeDetailSerializer

    def get_queryset(self):
        return (
            Resume.objects.filter(user=self.request.user)
            .select_related('analysis')
        )

    def perform_destroy(self, instance):
        # Delete file from storage as well
        if instance.file and os.path.isfile(instance.file.path):
            try:
                os.remove(instance.file.path)
            except OSError:
                pass
        instance.delete()


class ResumeAnalyzeView(views.APIView):
    """
    API endpoint to trigger or re-run AI evaluation for an existing resume.
    POST /api/v1/resumes/<id>/analyze/
    Optional payload: {"target_role": "Full Stack Engineer"}
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request, pk, *args, **kwargs):
        resume = get_object_or_404(Resume, pk=pk, user=request.user)

        serializer = ResumeAnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_role = serializer.validated_data.get('target_role', '').strip()

        if not target_role:
            career_profile = getattr(request.user, 'career_profile', None)
            if career_profile and career_profile.target_role:
                target_role = career_profile.target_role

        if not resume.extracted_text.strip():
            # If extracted_text was somehow empty, attempt to re-parse from file
            if resume.file:
                try:
                    resume.extracted_text, _ = DocumentParser.parse_file(resume.file)
                    resume.save(update_fields=['extracted_text'])
                except Exception as exc:
                    return Response(
                        {'detail': f"Unable to extract text from resume: {str(exc)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'detail': "Resume has no text content to analyze."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        analyzer = ResumeAnalyzer()
        try:
            analysis_data = analyzer.analyze_resume(
                resume_text=resume.extracted_text,
                target_role=target_role
            )
        except Exception as exc:
            return Response(
                {'detail': f"Analysis engine failure: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        analysis, created = ResumeAnalysis.objects.update_or_create(
            resume=resume,
            defaults={
                'target_role': target_role,
                'summary': analysis_data.get('summary', ''),
                'ats_score_estimate': analysis_data.get('ats_score_estimate', 0),
                'detected_skills': analysis_data.get('detected_skills', []),
                'missing_skills': analysis_data.get('missing_skills', []),
                'strengths': analysis_data.get('strengths', []),
                'weaknesses': analysis_data.get('weaknesses', []),
                'experience_summary': analysis_data.get('experience_summary', ''),
                'education_summary': analysis_data.get('education_summary', ''),
                'project_summary': analysis_data.get('project_summary', ''),
                'recommendations': analysis_data.get('recommendations', [])
            }
        )

        resp_serializer = ResumeAnalysisSerializer(analysis)
        resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(resp_serializer.data, status=resp_status)
