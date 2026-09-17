import os
from django.conf import settings
from rest_framework import serializers
from .models import Resume, ResumeAnalysis


class ResumeUploadSerializer(serializers.Serializer):
    """
    Validates uploaded resume file.
    Only PDF (.pdf) and Word (.docx) documents up to 5MB are permitted.
    """
    file = serializers.FileField(required=True)
    target_role = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1].lower()
        allowed_extensions = ['.pdf', '.docx']
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file format '{ext}'. Only PDF (.pdf) and Word (.docx) documents are supported."
            )

        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
        if value.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed limit of {max_mb:.0f}MB."
            )

        return value


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializes AI resume analysis and ATS compatibility evaluation.
    """
    ats_score_estimate = serializers.IntegerField(
        help_text="AI estimated ATS score (0-100)"
    )
    detected_skills = serializers.ListField(child=serializers.CharField(), read_only=True)
    missing_skills = serializers.ListField(child=serializers.CharField(), read_only=True)
    strengths = serializers.ListField(child=serializers.CharField(), read_only=True)
    weaknesses = serializers.ListField(child=serializers.CharField(), read_only=True)
    recommendations = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = ResumeAnalysis
        fields = [
            'id',
            'target_role',
            'summary',
            'ats_score_estimate',
            'detected_skills',
            'missing_skills',
            'strengths',
            'weaknesses',
            'experience_summary',
            'education_summary',
            'project_summary',
            'recommendations',
            'created_at',
        ]
        read_only_fields = fields


class ResumeListSerializer(serializers.ModelSerializer):
    """
    Lightweight resume representation for listing user resumes.
    """
    has_analysis = serializers.SerializerMethodField()
    ats_score_estimate = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            'id',
            'original_filename',
            'file',
            'file_type',
            'file_size',
            'has_analysis',
            'ats_score_estimate',
            'uploaded_at',
        ]
        read_only_fields = fields

    def get_has_analysis(self, obj):
        return hasattr(obj, 'analysis') and obj.analysis is not None

    def get_ats_score_estimate(self, obj):
        if hasattr(obj, 'analysis') and obj.analysis:
            return obj.analysis.ats_score_estimate
        return None


class ResumeDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive resume representation including extracted text and full analysis.
    """
    analysis = ResumeAnalysisSerializer(read_only=True)

    class Meta:
        model = Resume
        fields = [
            'id',
            'original_filename',
            'file',
            'file_type',
            'file_size',
            'extracted_text',
            'analysis',
            'uploaded_at',
            'updated_at',
        ]
        read_only_fields = fields


class ResumeAnalyzeRequestSerializer(serializers.Serializer):
    """
    Validates optional target_role for triggering an analysis.
    """
    target_role = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Target job title or role to tailor ATS evaluation against."
    )
