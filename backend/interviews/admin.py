from django.contrib import admin
from .models import InterviewAnswer, InterviewQuestion, InterviewSession


class InterviewQuestionInline(admin.TabularInline):
    model = InterviewQuestion
    extra = 0
    fields = ['question_number', 'question_type', 'question_text']


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'target_role', 'interview_type', 'difficulty', 'status', 'overall_score', 'created_at']
    list_filter = ['status', 'interview_type', 'difficulty', 'created_at']
    search_fields = ['user__email', 'target_role']
    inlines = [InterviewQuestionInline]


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'question_number', 'question_type']
    list_filter = ['question_type']
    search_fields = ['question_text']


@admin.register(InterviewAnswer)
class InterviewAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['answer_text', 'evaluation']
