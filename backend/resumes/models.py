import os
import uuid
from django.conf import settings
from django.db import models


def resume_upload_path(instance, filename):
    """
    Generate a secure, collision-free storage path for user resumes.
    Example: resumes/user_1/e4f2b...3a.pdf
    """
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('resumes', f"user_{instance.user_id}", unique_name)


class Resume(models.Model):
    """
    Uploaded resume document metadata and extracted raw text content.
    Strictly isolated per authenticated user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes'
    )
    file = models.FileField(upload_to=resume_upload_path)
    original_filename = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)
    file_type = models.CharField(max_length=10)  # 'pdf' or 'docx'
    file_size = models.PositiveIntegerField(help_text="File size in bytes")

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.email} - {self.original_filename} ({self.file_type})"


class ResumeAnalysis(models.Model):
    """
    Structured AI evaluation of an uploaded resume.
    ATS score is stored and explicitly presented as an AI-generated estimate.
    """
    resume = models.OneToOneField(
        Resume,
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    target_role = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    ats_score_estimate = models.PositiveIntegerField(
        default=0,
        help_text="Estimated ATS compatibility percentage (0-100)"
    )
    detected_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    experience_summary = models.TextField(blank=True)
    education_summary = models.TextField(blank=True)
    project_summary = models.TextField(blank=True)
    recommendations = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Resume Analyses'

    def __str__(self):
        return f"Analysis of {self.resume.original_filename} ({self.ats_score_estimate}%)"
