from django.urls import path
from .views import (
    JobDescriptionDetailView,
    JobDescriptionListCreateView,
    JobMatchCreateView,
    JobMatchDetailView,
    JobMatchListView,
)

urlpatterns = [
    path('', JobDescriptionListCreateView.as_view(), name='job-list-create'),
    path('matches/', JobMatchListView.as_view(), name='job-match-list'),
    path('matches/<int:pk>/', JobMatchDetailView.as_view(), name='job-match-detail'),
    path('<int:pk>/', JobDescriptionDetailView.as_view(), name='job-detail'),
    path('<int:pk>/match/', JobMatchCreateView.as_view(), name='job-match-create'),
]
