"""
llm.py
======
LLM integration using Groq.

Provides separate prompt strategies for different intents so that
the system prompt and instructions are always appropriate to the task.

Rules enforced in every prompt:
- Repository context is authoritative; no facts may be invented.
- Uncertainty must be stated explicitly.
- Sources must correspond to actual retrieved files.
- No fabricated code, files, or architecture details.
- Recommendations must be separated from confirmed findings.
"""
import logging

from groq import Groq
from httpx import Timeout

logger = logging.getLogger(__name__)

from app.config import get_settings

_SYSTEM_PROMPT = (
    "You are DevOS, an expert AI software engineering assistant. "
    "You analyze real repository code retrieved from a PostgreSQL index. "
    "Rules you MUST follow:\n"
    "1. Only use the provided repository context to make claims about the code.\n"
    "2. Never invent files, functions, classes, modules, or architecture details.\n"
    "3. If context is insufficient, clearly say so.\n"
    "4. Always distinguish: confirmed evidence / likely cause / possible cause / recommendation.\n"
    "5. Mention file paths and line numbers whenever they appear in the context.\n"
    "6. Never expose API keys, secrets, or .env file contents.\n"
)


class LLMService:

    def __init__(self):
        settings = get_settings()

        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(
            api_key=settings.GROQ_API_KEY,
            timeout=Timeout(25.0, connect=5.0),
        )
        self.model = settings.GROQ_MODEL

    # ------------------------------------------------------------------
    # Core generation method (used by /api/chat — unchanged behaviour)
    # ------------------------------------------------------------------

    def generate(self, question: str, context: str) -> str:
        prompt = (
            "Answer the user's question using the provided repository context.\n\n"
            f"Repository Context:\n{context}\n\n"
            f"User Question:\n{question}"
        )
        return self._call(prompt)

    # ------------------------------------------------------------------
    # Overview
    # ------------------------------------------------------------------

    def generate_overview(self, query: str, context: str) -> str:
        prompt = (
            "The user wants a high-level overview of this repository.\n"
            "Use ONLY the repository metadata and code samples below.\n"
            "Describe: purpose, languages, main directories, key files, frameworks detected.\n"
            "Do NOT invent any details not supported by the context.\n\n"
            f"Repository Context:\n{context}\n\n"
            f"User Question:\n{query}"
        )
        return self._call(prompt)

    # ------------------------------------------------------------------
    # Architecture
    # ------------------------------------------------------------------

    def generate_architecture(self, query: str, context: str) -> str:
        prompt = (
            "The user is asking an architecture or dependency question.\n"
            "Use ONLY the architecture map and code context below.\n"
            "Describe components, API routes, models, services, and their relationships.\n"
            "If a relationship is not in the context, say it could not be determined.\n\n"
            f"Architecture & Code Context:\n{context}\n\n"
            f"User Question:\n{query}"
        )
        return self._call(prompt)

    # ------------------------------------------------------------------
    # Bug analysis
    # ------------------------------------------------------------------

    def generate_bug_analysis(self, query: str, context: str) -> str:
        prompt = (
            "Perform a code review of the provided code.\n"
            "For each issue found:\n"
            "  - State the severity (high/medium/low)\n"
            "  - Quote the relevant code snippet from the context\n"
            "  - Explain why it is a potential problem\n"
            "  - Give a concrete recommendation\n"
            "IMPORTANT: Only report issues with direct evidence in the context.\n"
            "Never invent bugs not visible in the provided code.\n"
            "Separate confirmed issues from potential issues.\n\n"
            f"Code Context:\n{context}\n\n"
            f"User Request:\n{query}"
        )
        return self._call(prompt)

    # ------------------------------------------------------------------
    # Change plan
    # ------------------------------------------------------------------

    def generate_change_plan(self, query: str, context: str) -> str:
        prompt = (
            "Generate a structured change plan for the user's request. Output strictly valid JSON without any markdown formatting wrappers.\n"
            "Rules:\n"
            "  - Only reference files that appear in the provided context.\n"
            "  - Do NOT generate code that modifies arbitrary filesystem paths.\n"
            "  - If there is insufficient evidence to make a safe change, output empty changes.\n"
            "  - 'proposed_change' MUST contain the full exact replacement for the lines between start_line and end_line.\n"
            "Required JSON format:\n"
            "{\n"
            "  \"summary\": \"Overall explanation of the changes\",\n"
            "  \"changes\": [\n"
            "    {\n"
            "      \"file\": \"exact/path.py\",\n"
            "      \"start_line\": 1,\n"
            "      \"end_line\": 10,\n"
            "      \"reason\": \"Explanation of this change\",\n"
            "      \"proposed_change\": \"replacement code\"\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"Repository Context:\n{context}\n\n"
            f"User Request:\n{query}"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            e_str = str(e).lower()
            if "invalid_api_key" in e_str or "unauthorized" in e_str or "401" in e_str:
                raise ValueError("AI configuration error: Invalid API key") from None
            raise ValueError("AI service unavailable") from None

    # ------------------------------------------------------------------
    # General agent (DEBUG, EXPLAIN, IMPROVE, ANALYZE)
    # ------------------------------------------------------------------

    def generate_agent(self, intent: str, query: str, context: str) -> str:
        intent_instructions = {
            "DEBUG": (
                "Identify possible root causes of the described problem.\n"
                "Distinguish: confirmed evidence / likely cause / possible cause.\n"
                "Quote relevant code lines from the context.\n"
                "Suggest specific fixes, citing file paths and line numbers."
            ),
            "EXPLAIN": (
                "Explain clearly using only the provided code context.\n"
                "Walk through the relevant files and functions step by step.\n"
                "Cite file paths and line numbers for each claim."
            ),
            "IMPROVE_CODE": (
                "Suggest concrete improvements based on what you can see in the code.\n"
                "For each suggestion: explain the current behaviour, the problem, "
                "and the improvement. Cite file paths and line numbers."
            ),
            "ANALYZE_CODE": (
                "Analyze the retrieved code thoroughly.\n"
                "Describe what it does, how it works, its strengths and weaknesses.\n"
                "Cite file paths and line numbers for all observations."
            ),
        }
        instructions = intent_instructions.get(
            intent,
            "Answer the question using only the provided repository context.",
        )
        prompt = (
            f"{instructions}\n\n"
            f"Repository Context:\n{context}\n\n"
            f"User Question:\n{query}"
        )
        return self._call(prompt)

    # ------------------------------------------------------------------
    # Internal call
    # ------------------------------------------------------------------

    def _call(self, prompt: str) -> str:
        logger.info("LLM _call: sending request to Groq (model=%s)", self.model)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content or ""
            logger.info("LLM _call: response received (%d chars)", len(content))
            return content
        except Exception as e:
            e_str = str(e).lower()
            logger.error("LLM _call: Groq error — %s", type(e).__name__)
            if "invalid_api_key" in e_str or "unauthorized" in e_str or "401" in e_str:
                raise ValueError("AI configuration error: Invalid API key") from None
            if "model" in e_str and ("not found" in e_str or "does not exist" in e_str):
                raise ValueError(f"AI configuration error: model '{self.model}' not found") from None
            if "timeout" in e_str or "timed out" in e_str:
                raise ValueError("AI service timed out") from None
            raise ValueError(f"AI service unavailable: {type(e).__name__}") from None