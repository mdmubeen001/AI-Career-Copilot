from django.contrib import admin
from .models import Resume, ResumeAnalysis


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'original_filename', 'file_type', 'file_size', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('user__email', 'original_filename')


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'resume', 'target_role', 'ats_score_estimate', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('resume__user__email', 'resume__original_filename', 'target_role')
