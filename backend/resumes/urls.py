from django.urls import path
from .views import (
    ResumeAnalyzeView,
    ResumeDetailView,
    ResumeListView,
    ResumeUploadView,
)

urlpatterns = [
    path('upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('', ResumeListView.as_view(), name='resume-list'),
    path('<int:pk>/', ResumeDetailView.as_view(), name='resume-detail'),
    path('<int:pk>/analyze/', ResumeAnalyzeView.as_view(), name='resume-analyze'),
]
