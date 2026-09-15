from django.db import transaction
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from .models import CareerProfile, Skill, UserSkill
from .serializers import (
    CareerProfileSerializer,
    SkillSerializer,
    UserSkillSerializer,
)


class CareerProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to retrieve and update the authenticated user's career profile.
    Each user can only access their own career profile.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CareerProfileSerializer

    def get_object(self):
        profile, _ = CareerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'target_role': ''}
        )
        return profile


class SkillListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list existing skills and add new system skills.
    Requires authentication. Supports query parameter ?search= to filter skills.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SkillSerializer

    def get_queryset(self):
        queryset = Skill.objects.all().order_by('name')
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def create(self, request, *args, **kwargs):
        name = request.data.get('name', '').strip()
        if not name:
            return Response(
                {'name': ['Skill name cannot be empty.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing = Skill.objects.filter(name__iexact=name).first()
        if existing:
            serializer = self.get_serializer(existing)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data={'name': name})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserSkillListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and add skills for the authenticated user.
    All records are strictly scoped to the requesting user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSkillSerializer

    def get_queryset(self):
        return (
            UserSkill.objects.filter(user=self.request.user)
            .select_related('skill')
            .order_by('skill__name')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserSkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update level, or remove a skill for the authenticated user.
    Users cannot access or modify skills belonging to other users.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSkillSerializer

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user).select_related('skill')


class UserSkillBulkSyncView(views.APIView):
    """
    API endpoint to synchronize the authenticated user's entire skill set in one request.
    Accepts:
      {
        "skills": [
          {"name": "Python", "level": "Advanced"},
          "React",
          ...
        ]
      }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        raw_skills = request.data.get('skills', [])
        if not isinstance(raw_skills, list):
            return Response(
                {'skills': ['Expected a list of skills.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        valid_choices = dict(UserSkill.LEVEL_CHOICES)
        processed_skill_ids = set()

        with transaction.atomic():
            for item in raw_skills:
                if isinstance(item, str):
                    skill_name = item.strip()
                    level = 'Beginner'
                elif isinstance(item, dict):
                    skill_name = str(item.get('name', '')).strip()
                    level = item.get('level', 'Beginner')
                    if level not in valid_choices:
                        level = 'Beginner'
                else:
                    continue

                if not skill_name:
                    continue

                # Find or create skill
                skill = Skill.objects.filter(name__iexact=skill_name).first()
                if not skill:
                    skill = Skill.objects.create(name=skill_name)

                user_skill, _ = UserSkill.objects.update_or_create(
                    user=user,
                    skill=skill,
                    defaults={'level': level}
                )
                processed_skill_ids.add(user_skill.id)

            # Remove skills that are no longer present if a full sync was submitted
            # (only if raw_skills was explicitly provided and valid)
            UserSkill.objects.filter(user=user).exclude(id__in=processed_skill_ids).delete()

        current_skills = (
            UserSkill.objects.filter(user=user)
            .select_related('skill')
            .order_by('skill__name')
        )
        serializer = UserSkillSerializer(current_skills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
