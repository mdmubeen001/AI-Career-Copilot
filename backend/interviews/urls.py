from django.urls import path
from .views import (
    InterviewAnswerSubmitView,
    InterviewQuestionListView,
    InterviewSessionCompleteView,
    InterviewSessionDetailView,
    InterviewSessionListCreateView,
    InterviewSessionResultView,
    InterviewSessionStartView,
)

urlpatterns = [
    path('', InterviewSessionListCreateView.as_view(), name='interview-list-create'),
    path('<int:pk>/', InterviewSessionDetailView.as_view(), name='interview-detail'),
    path('<int:pk>/start/', InterviewSessionStartView.as_view(), name='interview-start'),
    path('<int:pk>/questions/', InterviewQuestionListView.as_view(), name='interview-questions'),
    path('<int:pk>/questions/<int:question_id>/answer/', InterviewAnswerSubmitView.as_view(), name='interview-answer-submit'),
    path('<int:pk>/complete/', InterviewSessionCompleteView.as_view(), name='interview-complete'),
    path('<int:pk>/result/', InterviewSessionResultView.as_view(), name='interview-result'),
]
