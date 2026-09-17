from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class InterviewSession(models.Model):
    """
    Represents an AI-driven interview session for an authenticated user.
    Tracks session configuration, target role, progress, and overall AI evaluation.
    """

    TYPE_CHOICES = [
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('mixed', 'Mixed'),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_sessions'
    )
    resume = models.ForeignKey(
        'resumes.Resume',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interview_sessions'
    )
    target_role = models.CharField(max_length=255)
    interview_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='mixed'
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='intermediate'
    )
    total_questions = models.PositiveIntegerField(default=5)
    current_question = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    overall_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI estimated overall interview readiness score (0-100)"
    )
    overall_feedback = models.TextField(blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.target_role} ({self.status})"


class InterviewQuestion(models.Model):
    """
    Individual question generated for an interview session.
    """

    QUESTION_TYPE_CHOICES = [
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('situational', 'Situational'),
    ]

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_number = models.PositiveIntegerField()
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='technical'
    )
    expected_topics = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_number']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'question_number'],
                name='unique_session_question_number'
            )
        ]

    def __str__(self):
        return f"Q{self.question_number} ({self.question_type}) - Session #{self.session_id}"


class InterviewAnswer(models.Model):
    """
    Candidate's submitted answer and its AI-evaluated score, strengths, and feedback.
    """

    question = models.OneToOneField(
        InterviewQuestion,
        on_delete=models.CASCADE,
        related_name='answer'
    )
    answer_text = models.TextField()
    score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI estimated score (0-100)"
    )
    evaluation = models.TextField(blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    missing_points = models.JSONField(default=list, blank=True)
    improvement_suggestions = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Answer for Q{self.question.question_number} - Score: {self.score}"
