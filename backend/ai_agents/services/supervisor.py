import logging
from .career_agent import CareerAgent

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent: Central orchestrator of the AI Multi-Agent system.
    Inspects user context, selects the appropriate specialized agent, executes it,
    validates the output, and prepares state for multi-agent workflows.
    """

    def __init__(self, career_agent: CareerAgent | None = None):
        self.career_agent = career_agent or CareerAgent()

    def handle_request(self, user, request_type: str = "career_analysis", context: dict | None = None) -> dict:
        """
        Main orchestration entrypoint.
        Routes to the designated specialized agent based on request_type.
        """
        context = context or {}

        # Build unified user context from user models
        user_context = self._build_user_context(user, context)

        if request_type == "career_analysis":
            return self._run_career_analysis(user_context)

        # Future agent routing hooks
        elif request_type in [
            "skill_gap_analysis",
            "learning_roadmap",
            "project_recommendation",
            "resume_optimization",
            "job_matching",
            "interview_prep",
            "flashcard_generation",
        ]:
            raise NotImplementedError(
                f"Agent workflow for '{request_type}' will be activated in an upcoming project phase."
            )
        else:
            raise ValueError(f"Unrecognized request_type: '{request_type}'.")

    def _build_user_context(self, user, extra_context: dict) -> dict:
        """
        Extract and merge context from user, accounts.Profile, career.CareerProfile, and career.UserSkill.
        """
        profile = getattr(user, 'profile', None)
        career_profile = getattr(user, 'career_profile', None)

        # Extract skills from career.UserSkill
        user_skills = []
        try:
            from career.models import UserSkill
            for us in UserSkill.objects.filter(user=user).select_related('skill'):
                user_skills.append({'name': us.skill.name, 'level': us.level})
        except Exception as e:
            logger.debug(f"Could not load UserSkill models: {e}")

        # Fallback to Profile.skills if UserSkill is empty
        if not user_skills and profile and profile.skills:
            for s in profile.skills:
                user_skills.append({'name': str(s), 'level': 'Intermediate'})

        # Determine target career goal (extra_context > career_profile.target_role > profile.career_goal)
        career_goal = (
            extra_context.get('career_goal')
            or (career_profile.target_role if career_profile and career_profile.target_role else '')
            or (profile.career_goal if profile and profile.career_goal else '')
            or 'Full Stack Developer'
        )

        return {
            'user_id': getattr(user, 'id', None),
            'email': getattr(user, 'email', ''),
            'full_name': profile.full_name if profile else '',
            'education': profile.education if profile else '',
            'college': profile.college if profile else '',
            'degree': profile.degree if profile else '',
            'graduation_year': profile.graduation_year if profile else None,
            'interests': profile.interests if profile else [],
            'current_role': career_profile.current_role if career_profile else '',
            'career_goal': career_goal,
            'experience_level': career_profile.experience_level if career_profile else 'Entry-level (0-2 years)',
            'bio': career_profile.bio if career_profile else '',
            'skills': user_skills,
            **extra_context  # Allow caller to override specific keys
        }

    def _run_career_analysis(self, user_context: dict) -> dict:
        """
        Execute Career Analysis agent and format output.
        """
        return self.career_agent.analyze_career(user_context)


# Global singleton instance for convenient view access
supervisor = SupervisorAgent()
