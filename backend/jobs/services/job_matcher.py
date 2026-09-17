import json
import logging
import re
from ai_agents.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class JobMatcher:
    """
    AI Job Matching Service:
    Evaluates candidate resume, career profile, and skills against a target Job Description.
    Reuses the central LLMService abstraction with an intelligent deterministic heuristic fallback.
    The match score is strictly an AI-generated estimate and not an official hiring/ATS score.
    """

    def __init__(self, llm_service: LLMService | None = None):
        self.llm = llm_service or LLMService()

    def match(self, resume, job_description, user=None) -> dict:
        """
        Execute job matching evaluation between a Resume and JobDescription.
        """
        user = user or resume.user
        profile = getattr(user, 'profile', None)
        career_profile = getattr(user, 'career_profile', None)
        resume_analysis = getattr(resume, 'analysis', None)

        # 1. Collect user and resume context
        user_skills = []
        try:
            from career.models import UserSkill
            for us in UserSkill.objects.filter(user=user).select_related('skill'):
                user_skills.append(us.skill.name)
        except Exception:
            pass

        if not user_skills and profile and profile.skills:
            user_skills = [str(s) for s in profile.skills]

        detected_resume_skills = []
        if resume_analysis and resume_analysis.detected_skills:
            detected_resume_skills = resume_analysis.detected_skills

        all_known_skills = list(set(user_skills + detected_resume_skills))

        candidate_context = {
            'target_role': getattr(career_profile, 'target_role', '') or getattr(profile, 'career_goal', ''),
            'current_role': getattr(career_profile, 'current_role', ''),
            'experience_level': getattr(career_profile, 'experience_level', 'Entry-level (0-2 years)'),
            'education': getattr(profile, 'education', '') or getattr(profile, 'degree', ''),
            'known_skills': all_known_skills,
            'resume_experience_summary': getattr(resume_analysis, 'experience_summary', '') if resume_analysis else '',
            'resume_education_summary': getattr(resume_analysis, 'education_summary', '') if resume_analysis else '',
        }

        job_context = {
            'title': job_description.title,
            'company': job_description.company or 'Not specified',
            'description': job_description.description,
            'source_url': job_description.source_url or '',
        }

        # 2. Build prompts for LLM
        system_prompt = (
            "You are an expert Technical Recruiter, Hiring Specialist, and Career Coach. "
            "Evaluate the candidate's resume and profile against the target job description. "
            "IMPORTANT: The match score is an AI-generated estimate to help candidates benchmark their preparation, "
            "NOT an official ATS or guaranteed hiring probability score. Do not fabricate skills or experience. "
            "Return a strictly valid JSON object matching this schema:\n"
            "{\n"
            '  "match_score_estimate": integer (0 to 100),\n'
            '  "summary": string,\n'
            '  "matching_skills": [string],\n'
            '  "missing_skills": [string],\n'
            '  "strengths": [string],\n'
            '  "gaps": [string],\n'
            '  "recommendations": [string]\n'
            "}"
        )

        user_prompt = (
            f"--- TARGET JOB DESCRIPTION ---\n"
            f"Title: {job_context['title']}\n"
            f"Company: {job_context['company']}\n"
            f"Description:\n{job_context['description'][:4000]}\n\n"
            f"--- CANDIDATE PROFILE & SKILLS ---\n"
            f"{json.dumps(candidate_context, indent=2)}\n\n"
            f"--- EXTRACTED RESUME TEXT ---\n"
            f"{resume.extracted_text[:4000]}\n\n"
            "Evaluate match alignment, matching competencies, missing requirements, strengths, gaps, and concrete recommendations."
        )

        # 3. Attempt LLM generation
        raw_result = self.llm.generate_json(user_prompt, system_prompt)
        if raw_result and isinstance(raw_result, dict):
            return self._sanitize_result(raw_result, job_description.title)

        # 4. Deterministic heuristic fallback
        return self._generate_heuristic_match(
            resume=resume,
            job_description=job_description,
            candidate_context=candidate_context,
            all_known_skills=all_known_skills
        )

    def _sanitize_result(self, data: dict, job_title: str) -> dict:
        """Sanitize and validate output fields and constraints."""
        try:
            score = int(data.get('match_score_estimate', 70))
            score = max(0, min(100, score))
        except (ValueError, TypeError):
            score = 70

        def clean_list(val, default):
            if isinstance(val, list):
                cleaned = [str(item).strip() for item in val if str(item).strip()]
                return cleaned if cleaned else default
            return default

        summary = str(data.get('summary', '')).strip()
        if not summary:
            summary = (
                f"Candidate demonstrates estimated {score}% alignment for the role of '{job_title}'. "
                f"Evaluation identifies key overlapping strengths alongside areas for targeted preparation."
            )

        return {
            'match_score_estimate': score,
            'summary': summary,
            'matching_skills': clean_list(data.get('matching_skills'), []),
            'missing_skills': clean_list(data.get('missing_skills'), []),
            'strengths': clean_list(data.get('strengths'), ['Strong foundational background for this domain.']),
            'gaps': clean_list(data.get('gaps'), ['Some specialized tools in the job description are not highlighted.']),
            'recommendations': clean_list(
                data.get('recommendations'),
                [f"Tailor resume bullet points to mirror keywords from '{job_title}'."]
            ),
        }

    def _generate_heuristic_match(
        self,
        resume,
        job_description,
        candidate_context: dict,
        all_known_skills: list
    ) -> dict:
        """
        Intelligent deterministic heuristic matcher when LLM is unconfigured or in mock mode.
        Extracts tech keywords from the job description and candidate resume,
        calculates overlap, checks experience indicators, and outputs structured evaluation.
        """
        jd_text = (job_description.title + " " + job_description.description).lower()
        resume_text = (resume.extracted_text or "").lower()

        # Extensive tech keyword taxonomy
        common_tech_skills = [
            'python', 'django', 'fastapi', 'flask', 'javascript', 'typescript', 'react',
            'vue', 'angular', 'next.js', 'node.js', 'express', 'html', 'css', 'tailwind',
            'sql', 'postgresql', 'mysql', 'sqlite', 'mongodb', 'redis', 'docker', 'kubernetes',
            'aws', 'gcp', 'azure', 'git', 'linux', 'ci/cd', 'rest api', 'graphql',
            'microservices', 'c++', 'java', 'spring', 'c#', '.net', 'go', 'golang', 'rust',
            'machine learning', 'deep learning', 'pytorch', 'tensorflow', 'pandas', 'numpy',
            'data structures', 'algorithms', 'agile', 'scrum', 'jira', 'unit testing', 'pytest'
        ]

        # 1. Identify skills demanded by Job Description
        jd_demanded_skills = []
        for skill in common_tech_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, jd_text):
                norm_name = skill.title() if len(skill) > 3 else skill.upper()
                jd_demanded_skills.append(norm_name)

        if not jd_demanded_skills:
            # Fallback to generic tech stack if no specific match
            jd_demanded_skills = ['Python', 'SQL', 'Git', 'REST API']

        # 2. Identify skills present in candidate resume / profile
        candidate_skills_lower = {s.lower() for s in all_known_skills}
        for skill in common_tech_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, resume_text):
                candidate_skills_lower.add(skill)

        # 3. Categorize matching vs missing skills
        matching_skills = []
        missing_skills = []
        for skill in jd_demanded_skills:
            if skill.lower() in candidate_skills_lower:
                matching_skills.append(skill)
            else:
                missing_skills.append(skill)

        # 4. Score calculation
        base_score = 45

        # Overlap ratio contribution (up to 35 points)
        if jd_demanded_skills:
            ratio = len(matching_skills) / len(jd_demanded_skills)
            base_score += int(ratio * 35)

        # Title keyword match (up to 8 points)
        title_keywords = [w for w in re.findall(r'\w+', job_description.title.lower()) if len(w) > 3]
        title_matches = sum(1 for w in title_keywords if w in resume_text)
        if title_matches > 0:
            base_score += min(8, title_matches * 3)

        # Experience indicators (up to 7 points)
        if any(w in resume_text for w in ['experience', 'work history', 'internship', 'developed', 'architected']):
            base_score += 5

        # Education match (up to 5 points)
        if any(w in resume_text for w in ['degree', 'b.s', 'bachelor', 'computer science', 'university']):
            base_score += 5

        final_score = max(25, min(95, base_score))

        # 5. Formulate Strengths
        strengths = []
        if matching_skills:
            strengths.append(f"Strong direct alignment on core job skills: {', '.join(matching_skills[:4])}.")
        if len(matching_skills) >= len(missing_skills) and len(matching_skills) > 0:
            strengths.append("High overall technical coverage across the requested stack.")
        if any(w in resume_text for w in ['project', 'github', 'portfolio']):
            strengths.append("Practical projects or application experience present in resume.")
        if not strengths:
            strengths.append("Demonstrated foundational engineering interest relevant to this position.")

        # 6. Formulate Gaps
        gaps = []
        if missing_skills:
            gaps.append(f"Missing high-priority keywords from job description: {', '.join(missing_skills[:4])}.")
        if not any(re.search(r'\b\d+%\b|\$\d+|\b\d+\s*(users|clients|requests)\b', resume_text) for _ in [0]):
            gaps.append("Lack of quantifiable business metrics (e.g. performance speedups, user volume, cost savings).")
        if not gaps:
            gaps.append("Resume could emphasize leadership or production architecture experience for this seniority.")

        # 7. Formulate Recommendations
        company_name = job_description.company or 'the hiring team'
        recommendations = [
            f"Tailor your resume summary to directly echo keywords from '{job_description.title}'.",
            f"Bridge priority skill gaps by featuring recent projects using: {', '.join(missing_skills[:3]) if missing_skills else 'System Design'}.",
            "Use active action verbs and quantify achievements with the Google XYZ formula: Accomplished [X] as measured by [Y], by doing [Z].",
            f"Prepare talking points demonstrating how your past experience relates to {company_name}'s specific requirements."
        ]

        summary = (
            f"Candidate profile demonstrates an estimated {final_score}% match compatibility for "
            f"'{job_description.title}'{f' at {job_description.company}' if job_description.company else ''}. "
            f"Identified {len(matching_skills)} verified overlapping competencies and {len(missing_skills)} key skill gaps "
            f"to bridge prior to application."
        )

        return {
            'match_score_estimate': final_score,
            'summary': summary,
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'strengths': strengths,
            'gaps': gaps,
            'recommendations': recommendations
        }
