import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


class LLMService:
    """
    Provider-independent LLM service supporting Gemini, OpenAI, and a safe local fallback.
    Never raises unhandled exceptions to avoid breaking downstream API endpoints.
    """

    def __init__(self):
        self.provider = os.environ.get('LLM_PROVIDER', 'mock').lower().strip()
        self.api_key = (
            os.environ.get('LLM_API_KEY')
            or os.environ.get('GEMINI_API_KEY')
            or os.environ.get('OPENAI_API_KEY')
            or ''
        ).strip()

    def generate_structured_analysis(self, prompt: str, system_prompt: str, context_data: dict) -> dict:
        """
        Generate a structured JSON analysis.
        Attempts remote LLM call if configured; gracefully falls back to the deterministic analytical engine.
        """
        if self.provider == 'gemini' and self.api_key:
            result = self._call_gemini(prompt, system_prompt)
            if result:
                return result

        if self.provider == 'openai' and self.api_key:
            result = self._call_openai(prompt, system_prompt)
            if result:
                return result

        # Default safe development fallback / mock engine
        return self._generate_contextual_fallback(context_data)

    def _call_gemini(self, prompt: str, system_prompt: str) -> dict | None:
        """Call Google Gemini API via REST."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_prompt}\n\nUser Profile & Goal:\n{prompt}"}]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.4
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status == 200:
                    resp_data = json.loads(response.read().decode('utf-8'))
                    text = resp_data['candidates'][0]['content']['parts'][0]['text']
                    return json.loads(text)
        except Exception as e:
            logger.warning(f"Gemini API call failed, using intelligent fallback: {e}")
            return None

    def _call_openai(self, prompt: str, system_prompt: str) -> dict | None:
        """Call OpenAI Chat Completions API via REST."""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.4
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status == 200:
                    resp_data = json.loads(response.read().decode('utf-8'))
                    text = resp_data['choices'][0]['message']['content']
                    return json.loads(text)
        except Exception as e:
            logger.warning(f"OpenAI API call failed, using intelligent fallback: {e}")
            return None

    def _generate_contextual_fallback(self, context_data: dict) -> dict:
        """
        Intelligent, deterministic rule-based analysis engine.
        Evaluates candidate's actual skills, education, and target goal to produce
        a realistic and helpful career analysis.
        """
        goal = context_data.get('career_goal') or 'Full Stack Software Engineer'
        skills = context_data.get('skills', [])
        normalized_skills = [
            (s.get('name') if isinstance(s, dict) else str(s)).strip().lower()
            for s in skills
            if s
        ]

        # Domain benchmark skillsets
        domain_benchmarks = {
            'ai': ['python', 'pytorch', 'tensorflow', 'machine learning', 'deep learning', 'math', 'sql'],
            'full stack': ['javascript', 'react', 'python', 'django', 'node.js', 'sql', 'html', 'css', 'git'],
            'backend': ['python', 'django', 'fastapi', 'sql', 'postgresql', 'docker', 'redis', 'system design'],
            'frontend': ['javascript', 'typescript', 'react', 'css', 'html', 'tailwind', 'next.js', 'ui/ux'],
            'devops': ['docker', 'kubernetes', 'linux', 'ci/cd', 'aws', 'terraform', 'python', 'bash'],
            'data': ['python', 'sql', 'pandas', 'spark', 'data modeling', 'statistics', 'tableau']
        }

        # Match goal to closest domain
        goal_lower = goal.lower()
        matched_domain = 'full stack'
        for key in domain_benchmarks:
            if key in goal_lower:
                matched_domain = key
                break

        benchmark = domain_benchmarks[matched_domain]

        # Categorize strengths (skills the candidate already possesses)
        raw_strengths = []
        for s in skills:
            name = s.get('name') if isinstance(s, dict) else str(s)
            if name.strip():
                raw_strengths.append(name.strip())

        strengths = raw_strengths[:5] if raw_strengths else ['Foundational Problem Solving', 'Adaptability']

        # Categorize weaknesses (benchmark skills not yet acquired)
        weaknesses = []
        for b in benchmark:
            if not any(b in s for s in normalized_skills):
                weaknesses.append(b.title())

        if not weaknesses:
            weaknesses = ['System Design & Scalability', 'Advanced Algorithmic Optimization', 'Cloud Infrastructure Automation']
        else:
            weaknesses = weaknesses[:4]

        # Calculate dynamic readiness score
        matched_count = sum(1 for b in benchmark if any(b in s for s in normalized_skills))
        base_score = 45
        skill_bonus = min(matched_count * 9, 45)
        experience_level = context_data.get('experience_level', '').lower()
        if 'senior' in experience_level or 'lead' in experience_level:
            exp_bonus = 10
        elif 'mid' in experience_level:
            exp_bonus = 6
        else:
            exp_bonus = 3

        readiness = min(max(base_score + skill_bonus + exp_bonus, 35), 94)

        # Generate adjacent career paths
        adjacent_map = {
            'ai': ['Machine Learning Engineer', 'AI Research Assistant', 'Data Scientist', 'LLM Application Engineer'],
            'full stack': ['Full Stack Developer', 'Backend Developer', 'Frontend Engineer', 'Python/React Specialist'],
            'backend': ['Backend Engineer', 'API Architect', 'Distributed Systems Engineer', 'Cloud Backend Specialist'],
            'frontend': ['Frontend Developer', 'UI Engineer', 'Client-Side Application Architect', 'Web Developer'],
            'devops': ['DevOps Engineer', 'Cloud Infrastructure Specialist', 'Site Reliability Engineer (SRE)', 'Platform Engineer'],
            'data': ['Data Analyst', 'Data Engineer', 'Business Intelligence Developer', 'Analytics Engineer']
        }
        recommended_paths = adjacent_map.get(matched_domain, [goal, 'Backend Engineer', 'Full Stack Developer'])

        # Detailed analysis narrative
        analysis_narrative = (
            f"Candidate profile shows promising alignment towards the target role of '{goal}'. "
            f"Based on your declared background in {context_data.get('education') or 'Computer Science / Engineering'} "
            f"and current proficiencies in {', '.join(strengths[:3]) if strengths else 'core fundamentals'}, "
            f"your estimated readiness stands at {readiness}%. "
            f"To accelerate progression towards senior-level competencies, priority should be given to closing identified gaps in "
            f"{', '.join(weaknesses[:3])}. Developing verifiable production projects and system architecture experience will provide the highest leverage."
        )

        # Actionable next steps
        next_actions = [
            f"Deepen proficiency in priority gap areas: {', '.join(weaknesses[:2])}.",
            f"Architect a full-scale portfolio project demonstrating production readiness for a {goal} position.",
            "Practice architectural system design, data modeling, and performance optimization scenarios.",
            "Refine technical interview readiness focusing on core data structures and domain-specific problem solving."
        ]

        return {
            "career_goal": goal,
            "career_readiness": readiness,
            "recommended_paths": recommended_paths,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "analysis": analysis_narrative,
            "next_actions": next_actions
        }
