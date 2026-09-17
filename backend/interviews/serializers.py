from rest_framework import serializers
from resumes.models import Resume
from .models import InterviewAnswer, InterviewQuestion, InterviewSession


class InterviewAnswerSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a submitted answer and its AI evaluation.
    """

    class Meta:
        model = InterviewAnswer
        fields = [
            'id',
            'question',
            'answer_text',
            'score',
            'evaluation',
            'strengths',
            'weaknesses',
            'missing_points',
            'improvement_suggestions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'question',
            'score',
            'evaluation',
            'strengths',
            'weaknesses',
            'missing_points',
            'improvement_suggestions',
            'created_at',
            'updated_at',
        ]


class InterviewAnswerSubmitSerializer(serializers.Serializer):
    """
    Input serializer for submitting candidate answer text.
    """
    answer_text = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            'blank': 'Answer text cannot be blank.',
            'required': 'Answer text is required.'
        }
    )

    def validate_answer_text(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Answer cannot be empty or only whitespace.")
        return cleaned


class InterviewQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for interview questions including candidate's answer if submitted.
    """
    answer = InterviewAnswerSerializer(read_only=True)

    class Meta:
        model = InterviewQuestion
        fields = [
            'id',
            'session',
            'question_number',
            'question_text',
            'question_type',
            'expected_topics',
            'created_at',
            'answer',
        ]
        read_only_fields = ['id', 'session', 'created_at']


class InterviewSessionCreateSerializer(serializers.Serializer):
    """
    Serializer to validate incoming request for creating a new interview session.
    """
    resume_id = serializers.IntegerField(required=False, allow_null=True)
    target_role = serializers.CharField(max_length=255, required=True, allow_blank=False)
    interview_type = serializers.ChoiceField(
        choices=InterviewSession.TYPE_CHOICES,
        default='mixed'
    )
    difficulty = serializers.ChoiceField(
        choices=InterviewSession.DIFFICULTY_CHOICES,
        default='intermediate'
    )
    total_questions = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        error_messages={
            'min_value': 'Total questions must be at least 1.',
            'max_value': 'Total questions cannot exceed 20.'
        }
    )

    def validate_target_role(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Target role cannot be blank.")
        return cleaned

    def validate_resume_id(self, value):
        if value is None:
            return None
        user = self.context.get('request').user
        if not Resume.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError(
                "Selected resume does not exist or does not belong to your account."
            )
        return value


class ResumeMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'original_filename', 'file_type']


class InterviewSessionSerializer(serializers.ModelSerializer):
    """
    Complete serializer for an interview session including questions and metadata.
    """
    resume = ResumeMinimalSerializer(read_only=True)
    questions = InterviewQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewSession
        fields = [
            'id',
            'target_role',
            'interview_type',
            'difficulty',
            'total_questions',
            'current_question',
            'status',
            'overall_score',
            'overall_feedback',
            'strengths',
            'weaknesses',
            'recommendations',
            'created_at',
            'updated_at',
            'resume',
            'questions',
        ]
        read_only_fields = fields


class InterviewSessionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing previous interview sessions on history/dashboard.
    """
    class Meta:
        model = InterviewSession
        fields = [
            'id',
            'target_role',
            'interview_type',
            'difficulty',
            'total_questions',
            'current_question',
            'status',
            'overall_score',
            'created_at',
        ]
        read_only_fields = fields


class InterviewResultSerializer(serializers.ModelSerializer):
    """
    Final evaluation output serializer.
    """
    questions = InterviewQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewSession
        fields = [
            'id',
            'target_role',
            'interview_type',
            'difficulty',
            'total_questions',
            'status',
            'overall_score',
            'overall_feedback',
            'strengths',
            'weaknesses',
            'recommendations',
            'created_at',
            'questions',
        ]
        read_only_fields = fields
