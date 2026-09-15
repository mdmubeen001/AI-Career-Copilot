import json
from .llm_service import LLMService


class CareerAgent:
    """
    Specialized Career Analysis Agent.
    Evaluates candidate background against target roles, identifies strengths and gaps,
    and produces structured career trajectory recommendations.
    """

    def __init__(self, llm_service: LLMService | None = None):
        self.llm = llm_service or LLMService()

    def analyze_career(self, profile_data: dict) -> dict:
        """
        Analyze candidate profile and return structured career assessment.
        """
        system_prompt = (
            "You are an elite AI Career Advisor and Systems Engineering Mentor. "
            "Analyze the candidate's career trajectory, education, skills, and target goal. "
            "Return a strictly valid JSON object matching this schema:\n"
            "{\n"
            '  "career_goal": string,\n'
            '  "career_readiness": integer (0 to 100),\n'
            '  "recommended_paths": [string],\n'
            '  "strengths": [string],\n'
            '  "weaknesses": [string],\n'
            '  "analysis": string,\n'
            '  "next_actions": [string]\n'
            "}"
        )

        user_prompt = (
            f"Candidate Profile:\n"
            f"- Target Role / Goal: {profile_data.get('career_goal', 'Software Engineer')}\n"
            f"- Current Role: {profile_data.get('current_role', 'Not specified')}\n"
            f"- Experience Level: {profile_data.get('experience_level', 'Not specified')}\n"
            f"- Education: {profile_data.get('education', 'Not specified')}\n"
            f"- Skills: {json.dumps(profile_data.get('skills', []))}\n"
            f"- Interests: {json.dumps(profile_data.get('interests', []))}\n"
            f"- Professional Bio: {profile_data.get('bio', '')}\n\n"
            "Provide a comprehensive, highly strategic evaluation with calibrated readiness score."
        )

        raw_result = self.llm.generate_structured_analysis(user_prompt, system_prompt, profile_data)
        return self._sanitize_result(raw_result, profile_data)

    def _sanitize_result(self, data: dict, fallback_context: dict) -> dict:
        """
        Ensure data conforms strictly to expected types and schema bounds.
        """
        if not isinstance(data, dict):
            data = {}

        # Career Goal
        career_goal = data.get('career_goal') or fallback_context.get('career_goal') or 'Software Engineer'

        # Readiness (clamped between 0 and 100)
        try:
            readiness = int(data.get('career_readiness', 50))
            readiness = max(0, min(100, readiness))
        except (ValueError, TypeError):
            readiness = 50

        # Lists
        def clean_list(val, default):
            if isinstance(val, list):
                return [str(item).strip() for item in val if str(item).strip()]
            return default

        recommended_paths = clean_list(data.get('recommended_paths'), [career_goal, 'Full Stack Developer', 'Backend Developer'])
        strengths = clean_list(data.get('strengths'), ['Adaptability', 'Foundational Competencies'])
        weaknesses = clean_list(data.get('weaknesses'), ['Advanced System Design', 'High-Scale Performance Tuning'])
        next_actions = clean_list(
            data.get('next_actions'),
            ['Build a production-grade portfolio project', 'Master system architecture patterns', 'Target specific interview skills']
        )

        analysis = str(data.get('analysis') or 'Comprehensive profile analysis completed. Refer to strengths and action items to optimize preparation.').strip()

        return {
            "career_goal": str(career_goal).strip(),
            "career_readiness": readiness,
            "recommended_paths": recommended_paths,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "analysis": analysis,
            "next_actions": next_actions
        }
