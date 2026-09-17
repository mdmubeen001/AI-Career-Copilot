from rest_framework import serializers
from .models import JobDescription, JobMatch
from resumes.models import Resume


class JobDescriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, listing, and retrieving user-owned Job Descriptions.
    Never accepts user from client; user is always set to request.user.
    """
    title = serializers.CharField(max_length=255)
    company = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField()
    source_url = serializers.URLField(max_length=500, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = JobDescription
        fields = [
            'id',
            'title',
            'company',
            'description',
            'source_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_title(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("Job title cannot be empty.")
        if len(normalized) < 2:
            raise serializers.ValidationError("Job title must be at least 2 characters long.")
        return normalized

    def validate_description(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("Job description cannot be empty.")
        if len(normalized) < 20:
            raise serializers.ValidationError("Job description must contain at least 20 characters.")
        return normalized

    def create(self, validated_data):
        user = validated_data.pop('user', None)
        if not user and 'request' in self.context:
            user = self.context['request'].user
        return JobDescription.objects.create(user=user, **validated_data)


class JobMatchRequestSerializer(serializers.Serializer):
    """
    Validates incoming request to trigger job matching.
    """
    resume_id = serializers.IntegerField(
        required=True,
        help_text="ID of the user's uploaded resume to evaluate against this job."
    )

    def validate_resume_id(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        resume = Resume.objects.filter(id=value, user=user).first()
        if not resume:
            raise serializers.ValidationError("Resume not found or does not belong to the current user.")
        return value


class JobMatchSerializer(serializers.ModelSerializer):
    """
    Full detail serializer for JobMatch evaluations.
    """
    job_title = serializers.CharField(source='job_description.title', read_only=True)
    company = serializers.CharField(source='job_description.company', read_only=True)
    resume_filename = serializers.CharField(source='resume.original_filename', read_only=True)
    matching_skills = serializers.ListField(child=serializers.CharField(), read_only=True)
    missing_skills = serializers.ListField(child=serializers.CharField(), read_only=True)
    strengths = serializers.ListField(child=serializers.CharField(), read_only=True)
    gaps = serializers.ListField(child=serializers.CharField(), read_only=True)
    recommendations = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = JobMatch
        fields = [
            'id',
            'job_description',
            'job_title',
            'company',
            'resume',
            'resume_filename',
            'match_score_estimate',
            'summary',
            'matching_skills',
            'missing_skills',
            'strengths',
            'gaps',
            'recommendations',
            'created_at',
        ]
        read_only_fields = fields


class JobMatchListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing user job matches.
    """
    job_title = serializers.CharField(source='job_description.title', read_only=True)
    company = serializers.CharField(source='job_description.company', read_only=True)
    resume_filename = serializers.CharField(source='resume.original_filename', read_only=True)

    class Meta:
        model = JobMatch
        fields = [
            'id',
            'job_description_id',
            'job_title',
            'company',
            'resume_id',
            'resume_filename',
            'match_score_estimate',
            'created_at',
        ]
        read_only_fields = fields
