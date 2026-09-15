from django.urls import path
from .views import (
    CareerAnalysisView,
    CareerAnalyzeView,
    CareerProfileView,
    SkillListCreateView,
    UserSkillBulkSyncView,
    UserSkillDetailView,
    UserSkillListCreateView,
)

app_name = 'career'

urlpatterns = [
    path('profile/', CareerProfileView.as_view(), name='career-profile'),
    path('skills/', SkillListCreateView.as_view(), name='skill-list-create'),
    path('user-skills/', UserSkillListCreateView.as_view(), name='user-skill-list-create'),
    path('user-skills/<int:pk>/', UserSkillDetailView.as_view(), name='user-skill-detail'),
    path('user-skills/sync/', UserSkillBulkSyncView.as_view(), name='user-skill-sync'),
    path('analyze/', CareerAnalyzeView.as_view(), name='career-analyze'),
    path('analysis/', CareerAnalysisView.as_view(), name='career-analysis'),
]
