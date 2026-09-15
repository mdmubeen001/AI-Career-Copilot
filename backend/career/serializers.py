from rest_framework import serializers
from .models import CareerAnalysis, CareerProfile, Skill, UserSkill


class SkillSerializer(serializers.ModelSerializer):
    """
    Serializer for available system skills.
    """
    class Meta:
        model = Skill
        fields = ['id', 'name']

    def validate_name(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("Skill name cannot be empty.")
        return normalized


class UserSkillSerializer(serializers.ModelSerializer):
    """
    Serializer for skills associated with the authenticated user,
    including proficiency level. Supports input by either skill name or ID.
    """
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    name = serializers.CharField(write_only=True, required=False)
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), source='skill', required=False, write_only=True
    )
    level = serializers.ChoiceField(
        choices=UserSkill.LEVEL_CHOICES,
        default='Beginner'
    )

    class Meta:
        model = UserSkill
        fields = ['id', 'skill', 'skill_name', 'name', 'skill_id', 'level']
        read_only_fields = ['id', 'skill', 'skill_name']

    def validate(self, attrs):
        name = attrs.get('name')
        skill = attrs.get('skill')
        if not name and not skill:
            raise serializers.ValidationError("Either 'skill_id' or 'name' must be provided.")
        return attrs

    def create(self, validated_data):
        user = validated_data.pop('user')
        level = validated_data.get('level', 'Beginner')
        name = validated_data.pop('name', None)
        skill = validated_data.pop('skill', None)

        if not skill and name:
            skill_name = name.strip()
            # Case-insensitive lookup or creation
            existing = Skill.objects.filter(name__iexact=skill_name).first()
            if existing:
                skill = existing
            else:
                skill = Skill.objects.create(name=skill_name)

        user_skill, _ = UserSkill.objects.update_or_create(
            user=user,
            skill=skill,
            defaults={'level': level}
        )
        return user_skill


class CareerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating user career profile details.
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    current_role = serializers.CharField(max_length=150, required=False, allow_blank=True)
    target_role = serializers.CharField(max_length=150, required=False, allow_blank=True)
    experience_level = serializers.CharField(max_length=50, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CareerProfile
        fields = [
            'id',
            'email',
            'current_role',
            'target_role',
            'experience_level',
            'bio',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']


class CareerAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer formatting stored CareerAnalysis instances matching the specified API schema.
    """
    career_goal = serializers.CharField(source='target_career_goal', read_only=True)
    career_readiness = serializers.IntegerField(source='career_readiness_estimate', read_only=True)
    recommended_paths = serializers.ListField(source='recommended_career_paths', child=serializers.CharField(), read_only=True)
    strengths = serializers.ListField(child=serializers.CharField(), read_only=True)
    weaknesses = serializers.ListField(child=serializers.CharField(), read_only=True)
    analysis = serializers.CharField(source='reasoning', read_only=True)
    next_actions = serializers.ListField(source='recommended_next_actions', child=serializers.CharField(), read_only=True)

    class Meta:
        model = CareerAnalysis
        fields = [
            'id',
            'career_goal',
            'career_readiness',
            'recommended_paths',
            'strengths',
            'weaknesses',
            'analysis',
            'next_actions',
            'current_education',
            'current_skills',
            'experience_level',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class CareerAnalyzeRequestSerializer(serializers.Serializer):
    """
    Serializer validating incoming request payload for POST /api/v1/career/analyze/.
    """
    career_goal = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Target career goal to evaluate against. If omitted, uses stored target role."
    )

