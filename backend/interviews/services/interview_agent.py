import json
import logging
import re
from typing import Any

from ai_agents.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class InterviewAgent:
    """
    AI Interview Agent responsible for:
    1. Question Generation tailored to role, candidate skills/resume, interview type, and difficulty.
    2. Answer Evaluation scoring correctness, depth, relevance, and missing points.
    3. Final Session Evaluation synthesizing individual answers into comprehensive feedback.
    Gracefully falls back to a deterministic heuristic engine when LLM providers are unavailable.
    """

    def __init__(self, llm_service: LLMService | None = None):
        self.llm = llm_service or LLMService()

    # =========================================================================
    # 1. QUESTION GENERATION
    # =========================================================================

    def generate_questions(
        self,
        target_role: str,
        interview_type: str = 'mixed',
        difficulty: str = 'intermediate',
        total_questions: int = 5,
        user: Any = None,
        resume: Any = None
    ) -> list[dict]:
        """
        Generate structured interview questions tailored to the candidate and role.
        """
        candidate_context = self._gather_candidate_context(user, resume)

        system_prompt = (
            "You are an expert Technical Interviewer, Hiring Manager, and Talent Assessor. "
            "Your task is to generate realistic, high-quality interview questions tailored to a specific role, "
            "difficulty level, interview type, and candidate profile.\n"
            "Rules:\n"
            f"1. Generate exactly {total_questions} questions.\n"
            f"2. Interview type: '{interview_type}' (if 'technical', only technical questions; if 'behavioral', only behavioral; if 'mixed', include technical, behavioral, and situational).\n"
            f"3. Difficulty: '{difficulty}'.\n"
            "4. Match question types to: 'technical', 'behavioral', or 'situational'.\n"
            "5. Include 2-4 expected topics or keywords that a strong candidate response should address.\n"
            "Return strictly valid JSON conforming to this schema:\n"
            "{\n"
            '  "questions": [\n'
            '    {\n'
            '      "question_number": 1,\n'
            '      "question_text": "...",\n'
            '      "question_type": "technical",\n'
            '      "expected_topics": ["topic1", "topic2"]\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        prompt = (
            f"Target Role: {target_role}\n"
            f"Interview Type: {interview_type}\n"
            f"Difficulty Level: {difficulty}\n"
            f"Total Questions Required: {total_questions}\n"
            f"Candidate Context: {json.dumps(candidate_context)}\n\n"
            "Generate questions that test both foundational knowledge and real-world execution."
        )

        raw_result = self.llm.generate_json(prompt, system_prompt)
        if raw_result and isinstance(raw_result, dict) and 'questions' in raw_result:
            validated = self._validate_questions(raw_result.get('questions'), total_questions, interview_type)
            if len(validated) == total_questions:
                return validated

        # Fallback to deterministic heuristic questions
        return self._generate_fallback_questions(
            target_role=target_role,
            interview_type=interview_type,
            difficulty=difficulty,
            total_questions=total_questions,
            candidate_context=candidate_context
        )

    # =========================================================================
    # 2. ANSWER EVALUATION
    # =========================================================================

    def evaluate_answer(
        self,
        question_text: str,
        question_type: str,
        expected_topics: list[str],
        answer_text: str,
        target_role: str = '',
        difficulty: str = 'intermediate'
    ) -> dict:
        """
        Evaluate a candidate's answer based on correctness, depth, relevance, and examples.
        Returns score (0-100), evaluation summary, strengths, weaknesses, missing points, and suggestions.
        """
        cleaned_answer = (answer_text or '').strip()
        if not cleaned_answer:
            return {
                "score": 0,
                "evaluation": "No answer was provided for this question.",
                "strengths": [],
                "weaknesses": ["Answer was left empty."],
                "missing_points": expected_topics or ["Detailed explanation", "Relevant examples"],
                "improvement_suggestions": ["Formulate a structured response covering core concepts with practical examples."]
            }

        system_prompt = (
            "You are an expert Technical Interview Evaluator. "
            "Evaluate the candidate's answer for the provided interview question objectively.\n"
            "Evaluate based on:\n"
            "- Correctness and technical accuracy\n"
            "- Relevance to the question prompt\n"
            "- Completeness and depth for the given difficulty level\n"
            "- Communication clarity and structure (e.g. STAR method for behavioral questions)\n"
            "- Concrete examples and mention of expected topics\n\n"
            "Important: The score is an AI evaluation estimate (0-100), not an official hiring decision.\n"
            "Return strictly valid JSON conforming to this schema:\n"
            "{\n"
            '  "score": 82,\n'
            '  "evaluation": "...",\n'
            '  "strengths": ["...", "..."],\n'
            '  "weaknesses": ["..."],\n'
            '  "missing_points": ["..."],\n'
            '  "improvement_suggestions": ["..."]\n'
            "}"
        )

        prompt = (
            f"Target Role: {target_role}\n"
            f"Difficulty: {difficulty}\n"
            f"Question Type: {question_type}\n"
            f"Question Text: {question_text}\n"
            f"Expected Topics/Keywords: {json.dumps(expected_topics)}\n"
            f"Candidate Answer:\n{cleaned_answer}\n\n"
            "Provide a precise, fair, and constructive evaluation."
        )

        raw_result = self.llm.generate_json(prompt, system_prompt)
        if raw_result and isinstance(raw_result, dict) and 'score' in raw_result:
            return self._sanitize_answer_evaluation(raw_result, expected_topics)

        # Fallback to heuristic answer evaluation
        return self._generate_fallback_answer_evaluation(
            question_text=question_text,
            question_type=question_type,
            expected_topics=expected_topics,
            answer_text=cleaned_answer,
            difficulty=difficulty
        )

    # =========================================================================
    # 3. FINAL SESSION EVALUATION
    # =========================================================================

    def evaluate_session(
        self,
        session_data: dict,
        answers_data: list[dict]
    ) -> dict:
        """
        Synthesize evaluations across all answered questions in the session.
        Calculates overall score, overall feedback, consolidated strengths, weaknesses, and recommendations.
        """
        if not answers_data:
            return {
                "overall_score": 0,
                "overall_feedback": "The session was concluded without any submitted answers.",
                "strengths": [],
                "weaknesses": ["No questions were answered."],
                "recommendations": ["Re-attempt the interview session and submit answers for all questions."]
            }

        scores = [a.get('score', 0) for a in answers_data if a.get('score') is not None]
        avg_score = int(round(sum(scores) / len(scores))) if scores else 0
        avg_score = max(0, min(100, avg_score))

        system_prompt = (
            "You are an executive Technical Hiring Director. "
            "Synthesize the candidate's complete interview performance into a comprehensive summary.\n"
            "Calculate an overall performance estimate and give actionable recommendations.\n"
            "Return strictly valid JSON conforming to this schema:\n"
            "{\n"
            '  "overall_score": 84,\n'
            '  "overall_feedback": "...",\n'
            '  "strengths": ["...", "..."],\n'
            '  "weaknesses": ["...", "..."],\n'
            '  "recommendations": ["...", "..."]\n'
            "}"
        )

        prompt = (
            f"Target Role: {session_data.get('target_role')}\n"
            f"Interview Type: {session_data.get('interview_type')}\n"
            f"Difficulty: {session_data.get('difficulty')}\n"
            f"Calculated Average Score: {avg_score}\n"
            f"Individual Question Evaluations:\n{json.dumps(answers_data)}\n\n"
            "Provide high-level constructive feedback and strategic preparation recommendations."
        )

        raw_result = self.llm.generate_json(prompt, system_prompt)
        if raw_result and isinstance(raw_result, dict) and 'overall_feedback' in raw_result:
            return self._sanitize_session_evaluation(raw_result, avg_score)

        # Fallback heuristic session synthesis
        return self._generate_fallback_session_evaluation(
            session_data=session_data,
            answers_data=answers_data,
            calculated_avg=avg_score
        )

    # =========================================================================
    # CONTEXT GATHERING & VALIDATION HELPERS
    # =========================================================================

    def _gather_candidate_context(self, user: Any, resume: Any) -> dict:
        """Extract profile, career goals, skills, and resume details."""
        context = {
            "skills": [],
            "education": "",
            "experience_level": "",
            "current_role": "",
            "resume_summary": "",
            "resume_skills": []
        }
        if not user:
            return context

        profile = getattr(user, 'profile', None)
        if profile:
            context["education"] = getattr(profile, 'education', '') or getattr(profile, 'degree', '')
            if getattr(profile, 'skills', None) and isinstance(profile.skills, list):
                context["skills"].extend(profile.skills)

        career_profile = getattr(user, 'career_profile', None)
        if career_profile:
            context["current_role"] = getattr(career_profile, 'current_role', '')
            context["experience_level"] = getattr(career_profile, 'experience_level', '')

        # UserSkill records
        if hasattr(user, 'userskill_set'):
            try:
                db_skills = user.userskill_set.select_related('skill').all()
                for us in db_skills:
                    context["skills"].append(f"{us.skill.name} ({us.level})")
            except Exception as e:
                logger.debug(f"Could not load UserSkill set: {e}")

        # Selected Resume / ResumeAnalysis
        if resume:
            context["resume_summary"] = getattr(resume, 'extracted_text', '')[:1000]
            analysis = getattr(resume, 'analysis', None)
            if analysis:
                context["resume_skills"] = getattr(analysis, 'detected_skills', [])

        return context

    def _validate_questions(self, raw_questions: Any, total: int, interview_type: str) -> list[dict]:
        """Validate and sanitize raw LLM question items."""
        if not isinstance(raw_questions, list):
            return []

        validated = []
        for i, q in enumerate(raw_questions[:total]):
            if not isinstance(q, dict):
                continue
            text = str(q.get('question_text', '')).strip()
            if not text:
                continue

            q_type = str(q.get('question_type', 'technical')).lower().strip()
            if q_type not in ('technical', 'behavioral', 'situational'):
                q_type = 'technical' if interview_type == 'technical' else 'behavioral'

            topics = q.get('expected_topics', [])
            if not isinstance(topics, list):
                topics = [str(topics)]
            clean_topics = [str(t).strip() for t in topics if str(t).strip()]

            validated.append({
                "question_number": i + 1,
                "question_text": text,
                "question_type": q_type,
                "expected_topics": clean_topics or ["Key concepts", "Best practices"]
            })

        return validated

    def _sanitize_answer_evaluation(self, data: dict, expected_topics: list[str]) -> dict:
        """Sanitize LLM answer evaluation dictionary."""
        try:
            score = int(data.get('score', 75))
            score = max(0, min(100, score))
        except (ValueError, TypeError):
            score = 75

        def clean_list(val, default):
            if isinstance(val, list):
                cleaned = [str(x).strip() for x in val if str(x).strip()]
                return cleaned if cleaned else default
            return default

        return {
            "score": score,
            "evaluation": str(data.get('evaluation', 'Candidate provided a structured response.')).strip(),
            "strengths": clean_list(data.get('strengths'), ["Addressed core aspects of the question."]),
            "weaknesses": clean_list(data.get('weaknesses'), ["Could provide more technical depth or real-world examples."]),
            "missing_points": clean_list(data.get('missing_points'), expected_topics[:2] if expected_topics else ["Edge-case handling"]),
            "improvement_suggestions": clean_list(data.get('improvement_suggestions'), ["Incorporate specific metrics and trade-offs into your explanation."])
        }

    def _sanitize_session_evaluation(self, data: dict, fallback_score: int) -> dict:
        """Sanitize LLM final session evaluation dictionary."""
        try:
            score = int(data.get('overall_score', fallback_score))
            score = max(0, min(100, score))
        except (ValueError, TypeError):
            score = fallback_score

        def clean_list(val, default):
            if isinstance(val, list):
                cleaned = [str(x).strip() for x in val if str(x).strip()]
                return cleaned if cleaned else default
            return default

        return {
            "overall_score": score,
            "overall_feedback": str(data.get('overall_feedback', 'Candidate demonstrated competent overall subject matter familiarity.')).strip(),
            "strengths": clean_list(data.get('strengths'), ["Clear technical fundamentals", "Structured responses"]),
            "weaknesses": clean_list(data.get('weaknesses'), ["Further depth in production edge cases"]),
            "recommendations": clean_list(data.get('recommendations'), ["Practice scenario-based architectural questions."])
        }

    # =========================================================================
    # DETERMINISTIC HEURISTIC FALLBACK ENGINES
    # =========================================================================

    def _generate_fallback_questions(
        self,
        target_role: str,
        interview_type: str,
        difficulty: str,
        total_questions: int,
        candidate_context: dict
    ) -> list[dict]:
        """
        Contextually generate interview questions based on target role, difficulty, and type.
        Supports Python/Django, Frontend/React, Data/AI, DevOps, and general software roles.
        """
        role_lower = target_role.lower()

        # Domain specific question pools
        if 'django' in role_lower or 'python' in role_lower:
            tech_pool = [
                {
                    "text": "How does the Django ORM handle database queries, and what strategies do you use to detect and eliminate N+1 query bottlenecks?",
                    "topics": ["select_related", "prefetch_related", "Django ORM", "SQL query optimization", "django-debug-toolbar"]
                },
                {
                    "text": "Explain how authentication and authorization are implemented in Django REST Framework. How do you customize permission classes and manage JWT expiration?",
                    "topics": ["JWT authentication", "permissions.BasePermission", "refresh tokens", "security headers"]
                },
                {
                    "text": "What are the core differences between synchronous Django views and asynchronous views or background worker tasks (e.g., Celery)? When would you choose one over the other?",
                    "topics": ["ASGI", "async views", "Celery", "Redis/RabbitMQ message brokers", "non-blocking I/O"]
                },
                {
                    "text": "How do Django database transactions and `transaction.atomic()` work? How do you ensure ACID compliance during complex multi-model updates?",
                    "topics": ["database transactions", "atomic decorator", "rollback behavior", "concurrency locks"]
                },
                {
                    "text": "Describe your approach to designing, versioning, and documenting RESTful APIs using Django REST Framework.",
                    "topics": ["API versioning", "serializers", "pagination", "OpenAPI/Swagger", "error handling standards"]
                },
                {
                    "text": "Explain how Python handles memory management, reference counting, and garbage collection, especially in long-running web processes.",
                    "topics": ["garbage collection", "reference counting", "cyclic references", "memory profiling"]
                }
            ]
        elif 'react' in role_lower or 'frontend' in role_lower or 'javascript' in role_lower:
            tech_pool = [
                {
                    "text": "Explain the React reconciliation algorithm and Virtual DOM diffing. How do you prevent unnecessary re-renders in performance-critical components?",
                    "topics": ["React reconciliation", "useMemo / useCallback", "React.memo", "virtual DOM", "keys in lists"]
                },
                {
                    "text": "Compare different state management patterns in modern React (e.g. Context API, Zustand, Redux). When is Context API sufficient versus an external store?",
                    "topics": ["Context API", "Zustand/Redux", "re-rendering overhead", "global vs local state"]
                },
                {
                    "text": "How do you optimize Core Web Vitals, specifically Largest Contentful Paint (LCP) and Cumulative Layout Shift (CLS) in a client-side React application?",
                    "topics": ["Core Web Vitals", "lazy loading", "code splitting", "image optimization", "skeleton loaders"]
                },
                {
                    "text": "Describe how you architect responsive, accessible UI layouts using CSS variables, flexbox, and grid while strictly adhering to WCAG standards.",
                    "topics": ["a11y", "ARIA attributes", "keyboard navigation", "color contrast", "responsive layout"]
                }
            ]
        elif 'data' in role_lower or 'ai' in role_lower or 'machine learning' in role_lower:
            tech_pool = [
                {
                    "text": "How do you handle data preprocessing, missing values, and high-cardinality categorical features in production data pipelines?",
                    "topics": ["imputation", "one-hot vs target encoding", "outlier detection", "pandas/NumPy"]
                },
                {
                    "text": "Explain the trade-offs between precision, recall, and F1-score. In what real-world scenarios would you prioritize recall over precision?",
                    "topics": ["precision/recall trade-off", "ROC-AUC", "confusion matrix", "class imbalance"]
                },
                {
                    "text": "Describe your strategy for evaluating and deploying Large Language Models (LLMs) with prompt engineering, RAG, and latency optimization.",
                    "topics": ["retrieval-augmented generation (RAG)", "vector databases", "embeddings", "context window management"]
                }
            ]
        else:
            # Generic Software Engineer
            tech_pool = [
                {
                    "text": "Describe the architectural patterns you apply when designing scalable, resilient backend web services under high concurrency.",
                    "topics": ["caching strategies", "database indexing", "load balancing", "horizontal scaling", "rate limiting"]
                },
                {
                    "text": "How do you design and structure unit, integration, and end-to-end tests to guarantee high system reliability without slowing CI/CD velocity?",
                    "topics": ["test pyramid", "mocking external services", "integration testing", "CI/CD pipelines"]
                },
                {
                    "text": "Explain how relational database indexing (B-Trees) works and what factors you examine when diagnosing a slow query in production.",
                    "topics": ["EXPLAIN ANALYZE", "B-Tree indexes", "composite indexes", "table scans"]
                }
            ]

        behavioral_pool = [
            {
                "text": "Tell me about a challenging technical bug or outage you encountered in production. How did you isolate the root cause, communicate with stakeholders, and prevent recurrence?",
                "topics": ["incident management", "root cause analysis (RCA)", "post-mortem", "stakeholder communication"]
            },
            {
                "text": "Describe a scenario where you had a significant technical disagreement with a team member or architect regarding implementation direction. How did you resolve it?",
                "topics": ["constructive debate", "data-driven decisions", "compromise", "active listening"]
            },
            {
                "text": "Can you give an example of a project where requirements shifted unexpectedly close to a major release deadline? How did you prioritize tasks to deliver value?",
                "topics": ["scope management", "agile prioritization", "adaptability", "deadline management"]
            },
            {
                "text": "How do you approach mentoring junior engineers, onboarding new teammates, and fostering a culture of high code quality and peer review?",
                "topics": ["code review standards", "empathy", "knowledge sharing", "engineering culture"]
            }
        ]

        situational_pool = [
            {
                "text": "You notice an API endpoint's response time is steadily degrading from 200ms to 4.5 seconds during peak traffic hours. Walk through your step-by-step diagnostic workflow.",
                "topics": ["APM/profiling metrics", "database connection pools", "slow query logs", "caching layer", "system resource bottlenecks"]
            },
            {
                "text": "A critical third-party service provider goes down intermittently, causing cascading timeouts in your core checkout or user workflow. What immediate and long-term mitigations do you implement?",
                "topics": ["circuit breakers", "retry policies with exponential backoff", "graceful degradation", "fallback responses"]
            },
            {
                "text": "You are tasked with migrating a legacy database schema with zero scheduled downtime while handling active read/write user traffic. How do you plan and execute the migration?",
                "topics": ["blue/green deployment", "dual-writing", "backward-compatible schema changes", "data verification"]
            }
        ]

        questions = []
        tech_idx, beh_idx, sit_idx = 0, 0, 0

        for num in range(1, total_questions + 1):
            if interview_type == 'technical':
                selected_pool = tech_pool
                q_type = 'technical'
                item = selected_pool[tech_idx % len(selected_pool)]
                tech_idx += 1
            elif interview_type == 'behavioral':
                selected_pool = behavioral_pool
                q_type = 'behavioral'
                item = selected_pool[beh_idx % len(selected_pool)]
                beh_idx += 1
            else:
                # Mixed: Alternate technical, behavioral, and situational
                mod = (num - 1) % 3
                if mod == 0:
                    selected_pool = tech_pool
                    q_type = 'technical'
                    item = selected_pool[tech_idx % len(selected_pool)]
                    tech_idx += 1
                elif mod == 1:
                    selected_pool = behavioral_pool
                    q_type = 'behavioral'
                    item = selected_pool[beh_idx % len(selected_pool)]
                    beh_idx += 1
                else:
                    selected_pool = situational_pool
                    q_type = 'situational'
                    item = selected_pool[sit_idx % len(selected_pool)]
                    sit_idx += 1

            # Adjust difficulty tone if advanced
            prefix = ""
            if difficulty == 'advanced' and q_type == 'technical':
                prefix = "At an enterprise architectural scale: "
            elif difficulty == 'beginner' and q_type == 'technical':
                prefix = "From a foundational perspective: "

            questions.append({
                "question_number": num,
                "question_text": f"{prefix}{item['text']}",
                "question_type": q_type,
                "expected_topics": item['topics']
            })

        return questions

    def _generate_fallback_answer_evaluation(
        self,
        question_text: str,
        question_type: str,
        expected_topics: list[str],
        answer_text: str,
        difficulty: str
    ) -> dict:
        """
        Rule-based analytical answer evaluator for fallback mode.
        Analyzes answer length, keyword alignment against expected topics, structure, and depth.
        """
        lower_ans = answer_text.lower()
        words = re.findall(r'\b\w+\b', lower_ans)
        word_count = len(words)

        # Baseline evaluation based on length
        if word_count < 10:
            score = 35
            depth_eval = "The answer is extremely brief and lacks necessary context and technical explanation."
        elif word_count < 30:
            score = 55
            depth_eval = "The answer introduces initial concepts but requires substantially more depth and concrete examples."
        elif word_count < 80:
            score = 75
            depth_eval = "Good, structured answer covering the core principles."
        else:
            score = 88
            depth_eval = "Comprehensive, detailed explanation demonstrating thorough understanding."

        # Keyword matching against expected topics
        matched_topics = []
        missing_topics = []
        for topic in expected_topics:
            topic_tokens = re.findall(r'\b\w+\b', topic.lower())
            if any(tok in lower_ans for tok in topic_tokens if len(tok) > 3):
                matched_topics.append(topic)
            else:
                missing_topics.append(topic)

        # Adjust score according to topic coverage
        if expected_topics:
            match_ratio = len(matched_topics) / len(expected_topics)
            score = int(round(score * 0.6 + (match_ratio * 100) * 0.4))

        # Adjust for difficulty expectation
        if difficulty == 'advanced' and word_count < 50:
            score = max(score - 10, 40)
        elif difficulty == 'beginner':
            score = min(score + 5, 95)

        score = max(10, min(95, score))

        strengths = []
        if matched_topics:
            strengths.append(f"Successfully addressed key concepts: {', '.join(matched_topics[:3])}.")
        if word_count >= 40:
            strengths.append("Provided articulated technical context and systematic thought process.")
        else:
            strengths.append("Direct and concise focus on the core subject.")

        weaknesses = []
        if missing_topics:
            weaknesses.append(f"Omitted important topic dimensions: {', '.join(missing_topics[:2])}.")
        if word_count < 40:
            weaknesses.append("Response would benefit from greater elaboration on production tradeoffs.")

        missing_points = missing_topics if missing_topics else [
            "Discussion of production edge cases",
            "Quantifiable metrics or performance considerations"
        ]

        improvement_suggestions = [
            f"Explicitly weave in discussion of: {missing_points[0]}.",
            "Use the STAR framework (Situation, Task, Action, Result) when describing real-world scenarios.",
            "Quantify trade-offs (e.g. latency impact, memory footprint, maintenance complexity)."
        ]

        return {
            "score": score,
            "evaluation": f"{depth_eval} The response scored {score}/100 based on keyword coverage and structural clarity.",
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_points": missing_points,
            "improvement_suggestions": improvement_suggestions
        }

    def _generate_fallback_session_evaluation(
        self,
        session_data: dict,
        answers_data: list[dict],
        calculated_avg: int
    ) -> dict:
        """
        Synthesize session feedback across individual answers for fallback mode.
        """
        target_role = session_data.get('target_role', 'Target Role')
        difficulty = session_data.get('difficulty', 'intermediate')

        # Aggregate strengths & weaknesses
        all_strengths = []
        all_weaknesses = []
        for ans in answers_data:
            all_strengths.extend(ans.get('strengths', []))
            all_weaknesses.extend(ans.get('weaknesses', []))

        # Unique preserving order
        unique_strengths = list(dict.fromkeys(all_strengths))[:4]
        unique_weaknesses = list(dict.fromkeys(all_weaknesses))[:4]

        if not unique_strengths:
            unique_strengths = [
                "Demonstrated fundamental domain familiarity",
                "Structured communication throughout the session"
            ]
        if not unique_weaknesses:
            unique_weaknesses = [
                "Deepen discussion around high-concurrency production architectures",
                "Integrate more quantitative outcome metrics into scenario answers"
            ]

        feedback = (
            f"Candidate completed {len(answers_data)} interview questions for the '{target_role}' role "
            f"at the {difficulty} level with an estimated readiness score of {calculated_avg}/100. "
            f"Overall, responses demonstrated solid foundational competency. "
            f"To reach elite tier readiness, focus on closing the identified gaps in "
            f"{unique_weaknesses[0] if unique_weaknesses else 'complex system trade-offs'}."
        )

        recommendations = [
            f"Review and practice deep-dive technical explanations for {target_role} system design.",
            "Formulate 3-4 structured STAR stories detailing challenging technical production incidents.",
            "Study specific failure modes, error handling, and performance profiling tools.",
            "Re-attempt practice interview sessions to refine answer timing and clarity."
        ]

        return {
            "overall_score": calculated_avg,
            "overall_feedback": feedback,
            "strengths": unique_strengths,
            "weaknesses": unique_weaknesses,
            "recommendations": recommendations
        }
