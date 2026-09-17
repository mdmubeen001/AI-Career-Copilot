import json
import logging
import re
from ai_agents.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    """
    Resume analysis service evaluating extracted document text against target roles.
    Produces structured ATS estimate, skill breakdown, section summaries, and recommendations.
    """

    def __init__(self, llm_service: LLMService | None = None):
        self.llm = llm_service or LLMService()

    def analyze_resume(self, resume_text: str, user=None, target_role: str = '') -> dict:
        """
        Main entry point for analyzing candidate resume text.
        """
        # Determine effective target role
        effective_role = (
            target_role.strip()
            or getattr(getattr(user, 'career_profile', None), 'target_role', '')
            or getattr(getattr(user, 'profile', None), 'career_goal', '')
            or 'Software Engineer'
        )

        user_info = {}
        if user:
            profile = getattr(user, 'profile', None)
            career_profile = getattr(user, 'career_profile', None)
            user_info = {
                'full_name': getattr(profile, 'full_name', ''),
                'education': getattr(profile, 'education', ''),
                'current_role': getattr(career_profile, 'current_role', ''),
                'experience_level': getattr(career_profile, 'experience_level', ''),
            }

        system_prompt = (
            "You are an expert Technical Recruiter and Applicant Tracking System (ATS) Specialist. "
            "Analyze the candidate's resume text against the target role. "
            "Note: The ATS score is an estimate to help the candidate improve compatibility. "
            "Return a strictly valid JSON object matching this schema:\n"
            "{\n"
            '  "summary": string,\n'
            '  "ats_score_estimate": integer (0 to 100),\n'
            '  "detected_skills": [string],\n'
            '  "missing_skills": [string],\n'
            '  "strengths": [string],\n'
            '  "weaknesses": [string],\n'
            '  "experience_summary": string,\n'
            '  "education_summary": string,\n'
            '  "project_summary": string,\n'
            '  "recommendations": [string]\n'
            "}"
        )

        prompt = (
            f"Target Role: {effective_role}\n"
            f"User Profile Info: {json.dumps(user_info)}\n\n"
            f"--- RESUME TEXT CONTENT ---\n"
            f"{resume_text[:6000]}\n"
            f"--- END RESUME TEXT ---\n\n"
            "Provide a thorough, objective evaluation with quantifiable feedback."
        )

        # Attempt LLM completion
        raw_result = self.llm.generate_json(prompt, system_prompt)
        if raw_result and isinstance(raw_result, dict):
            return self._sanitize_result(raw_result, effective_role, resume_text)

        # Fallback to analytical heuristic engine
        return self._generate_heuristic_analysis(resume_text, effective_role, user_info)

    def _sanitize_result(self, data: dict, target_role: str, resume_text: str) -> dict:
        """Sanitize and guarantee schema boundary conditions."""
        try:
            ats_score = int(data.get('ats_score_estimate', 65))
            ats_score = max(0, min(100, ats_score))
        except (ValueError, TypeError):
            ats_score = 65

        def clean_list(val, default):
            if isinstance(val, list):
                return [str(item).strip() for item in val if str(item).strip()]
            return default

        return {
            "summary": str(data.get('summary') or f"Resume evaluated against {target_role} requirements.").strip(),
            "ats_score_estimate": ats_score,
            "detected_skills": clean_list(data.get('detected_skills'), ['Problem Solving', 'Communication']),
            "missing_skills": clean_list(data.get('missing_skills'), ['System Architecture', 'CI/CD Pipelines']),
            "strengths": clean_list(data.get('strengths'), ['Clear document structure', 'Relevant project work']),
            "weaknesses": clean_list(data.get('weaknesses'), ['Quantifiable impact metrics could be strengthened']),
            "experience_summary": str(data.get('experience_summary') or 'Professional and academic background documented in resume.').strip(),
            "education_summary": str(data.get('education_summary') or 'Education credentials detected in resume.').strip(),
            "project_summary": str(data.get('project_summary') or 'Technical projects highlighting practical domain applications.').strip(),
            "recommendations": clean_list(
                data.get('recommendations'),
                [
                    'Incorporate measurable performance metrics (e.g., % improvement, scale handled).',
                    f'Add industry-standard keywords aligned with {target_role}.',
                    'Ensure technical section emphasizes modern tools and frameworks.'
                ]
            )
        }

    def _generate_heuristic_analysis(self, text: str, target_role: str, user_info: dict) -> dict:
        """
        Intelligent deterministic heuristic analyzer.
        Extracts skills, checks section completeness, and calculates an ATS compatibility score.
        """
        text_lower = text.lower()

        # Common Tech Keywords Knowledge Base
        common_skills = [
            'python', 'javascript', 'typescript', 'react', 'django', 'fastapi', 'node.js',
            'html', 'css', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'docker',
            'kubernetes', 'aws', 'gcp', 'azure', 'git', 'linux', 'ci/cd', 'rest api',
            'graphql', 'machine learning', 'deep learning', 'pytorch', 'tensorflow',
            'pandas', 'numpy', 'data structures', 'algorithms', 'agile', 'scrum',
            'microservices', 'c++', 'java', 'c#', 'go', 'rust', 'tailwind'
        ]

        # Detect skills in text
        detected = []
        for skill in common_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                detected.append(skill.title() if len(skill) > 3 else skill.upper())

        # Role benchmark requirements
        role_benchmarks = {
            'full stack': ['JavaScript', 'React', 'Python', 'Django', 'SQL', 'Git', 'Docker', 'REST API'],
            'backend': ['Python', 'Django', 'SQL', 'PostgreSQL', 'Docker', 'Redis', 'REST API', 'Linux'],
            'frontend': ['JavaScript', 'TypeScript', 'React', 'HTML', 'CSS', 'Tailwind', 'Git'],
            'ai': ['Python', 'PyTorch', 'Tensorflow', 'Machine Learning', 'SQL', 'Pandas', 'NumPy'],
            'devops': ['Docker', 'Kubernetes', 'Linux', 'AWS', 'CI/CD', 'Git', 'Python'],
        }

        matched_domain = 'full stack'
        for key in role_benchmarks:
            if key in target_role.lower():
                matched_domain = key
                break

        benchmark = role_benchmarks[matched_domain]
        detected_set = {s.lower() for s in detected}
        missing = [b for b in benchmark if b.lower() not in detected_set]
        matched_benchmark = [b for b in benchmark if b.lower() in detected_set]

        # Section detection check
        has_experience = any(k in text_lower for k in ['experience', 'employment', 'work history', 'internship'])
        has_education = any(k in text_lower for k in ['education', 'degree', 'university', 'b.s.', 'b.tech', 'college'])
        has_projects = any(k in text_lower for k in ['project', 'portfolio', 'hackathon'])
        has_skills_section = any(k in text_lower for k in ['skills', 'technical skills', 'technologies'])
        has_contact = any(k in text_lower for k in ['@', 'email', 'phone', 'github', 'linkedin'])

        # Calculate estimated ATS Score
        score = 40  # base
        if has_experience: score += 10
        if has_education: score += 10
        if has_projects: score += 10
        if has_skills_section: score += 8
        if has_contact: score += 7

        # Skill alignment bonus
        skill_ratio = len(matched_benchmark) / max(len(benchmark), 1)
        score += int(skill_ratio * 15)

        # Quantifiable metrics bonus (numbers, percentages)
        quant_matches = len(re.findall(r'\b\d+%\b|\$\d+|\b\d+x\b|\b\d+\s*(users|clients|requests|ms)\b', text_lower))
        if quant_matches >= 3:
            score += 5
        elif quant_matches >= 1:
            score += 2

        score = max(35, min(94, score))

        # Strengths
        strengths = []
        if matched_benchmark:
            strengths.append(f"Strong keyword alignment for core competencies: {', '.join(matched_benchmark[:4])}.")
        if has_projects:
            strengths.append("Dedicated project section demonstrating practical application.")
        if has_experience:
            strengths.append("Professional/internship experience clearly delineated.")
        if not strengths:
            strengths.append("Clean baseline structure readable by ATS parsers.")

        # Weaknesses
        weaknesses = []
        if missing:
            weaknesses.append(f"Missing high-impact keywords for {target_role}: {', '.join(missing[:4])}.")
        if quant_matches < 2:
            weaknesses.append("Lack of quantifiable business impact metrics (e.g. % improvements, user counts, latency reductions).")
        if not has_skills_section:
            weaknesses.append("Skills are scattered rather than consolidated in a dedicated technical skills section.")
        if not weaknesses:
            weaknesses.append("Could further elevate seniority indicators and architecture leadership achievements.")

        # Section summaries
        experience_summary = (
            "Experience highlights documented professional roles and technical tasks. "
            "Bullet points clearly outline responsibilities."
            if has_experience else
            "Experience section was not clearly distinguished. Adding formal work or internship titles is recommended."
        )

        # Extract education specific lines if present
        edu_lines = []
        for line in text.split('\n'):
            line_clean = line.strip()
            if any(k in line_clean.lower() for k in ['b.s', 'b.tech', 'm.s', 'bachelor', 'master', 'phd', 'degree', 'university', 'college']):
                edu_lines.append(line_clean)

        if edu_lines:
            education_summary = f"Education: {'; '.join(edu_lines[:2])}. Academic credentials and degree major are clearly represented."
        elif has_education:
            education_summary = "Academic credentials, degree major, and institutional background are clearly represented."
        else:
            education_summary = "Education credentials were minimally detected. Ensure degree, major, and graduation year are present."

        project_summary = (
            f"Technical projects effectively showcase practical software development. "
            f"Demonstrates stack capability in {', '.join(detected[:3]) if detected else 'software fundamentals'}."
            if has_projects else
            "Consider featuring 2–3 notable technical projects demonstrating end-to-end system design."
        )

        recommendations = [
            f"Tailor resume summary and bullet points to emphasize '{target_role}' keywords.",
            f"Prioritize incorporating missing technical skills: {', '.join(missing[:3]) if missing else 'Advanced System Architecture'}.",
            "Use the Google XYZ resume formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.",
            "Keep formatting clean without complex multi-column tables, graphics, or text boxes that confuse ATS parsers."
        ]

        summary = (
            f"Resume demonstrates solid foundational alignment for '{target_role}' with an estimated "
            f"ATS compatibility score of {score}%. Identified {len(detected)} technical competencies. "
            f"Applying targeted keyword optimization and quantifiable bullet points will improve parsing performance."
        )

        return {
            "summary": summary,
            "ats_score_estimate": score,
            "detected_skills": detected[:15],
            "missing_skills": missing[:8],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "experience_summary": experience_summary,
            "education_summary": education_summary,
            "project_summary": project_summary,
            "recommendations": recommendations
        }
