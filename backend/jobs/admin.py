from django.contrib import admin
from .models import JobDescription, JobMatch


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'user', 'created_at')
    search_fields = ('title', 'company', 'user__email', 'description')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_title', 'user', 'match_score_estimate', 'created_at')
    search_fields = ('job_description__title', 'job_description__company', 'user__email', 'summary')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

    def job_title(self, obj):
        return obj.job_description.title
    job_title.short_description = 'Job Title'
