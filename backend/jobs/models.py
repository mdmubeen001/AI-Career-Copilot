from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class JobDescription(models.Model):
    """
    Target job description supplied by a user for analysis and matching.
    Strictly isolated per authenticated user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_descriptions'
    )
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    source_url = models.URLField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        company_str = f" at {self.company}" if self.company else ""
        return f"{self.title}{company_str} ({self.user.email})"


class JobMatch(models.Model):
    """
    Structured AI evaluation matching an uploaded Resume against a Job Description.
    The match score is explicitly labeled and stored as an AI-generated estimate,
    not an official hiring or ATS score.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_matches'
    )
    resume = models.ForeignKey(
        'resumes.Resume',
        on_delete=models.CASCADE,
        related_name='job_matches'
    )
    job_description = models.ForeignKey(
        JobDescription,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    match_score_estimate = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI estimated match compatibility percentage (0-100)"
    )
    summary = models.TextField()
    matching_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    gaps = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Job Matches'

    def clean(self):
        super().clean()
        if self.resume_id and self.user_id and self.resume.user_id != self.user_id:
            raise ValidationError("Resume must belong to the authenticated user.")
        if self.job_description_id and self.user_id and self.job_description.user_id != self.user_id:
            raise ValidationError("Job description must belong to the authenticated user.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Match: {self.job_description.title} - Score: {self.match_score_estimate}% ({self.user.email})"
