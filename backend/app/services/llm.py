"""
llm.py
======
LLM integration using Groq and Gemini.

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
from abc import ABC, abstractmethod

from groq import Groq
from httpx import Timeout
import google.generativeai as genai

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


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, question: str, context: str) -> str:
        pass

    @abstractmethod
    def generate_overview(self, query: str, context: str) -> str:
        pass

    @abstractmethod
    def generate_architecture(self, query: str, context: str) -> str:
        pass

    @abstractmethod
    def generate_bug_analysis(self, query: str, context: str) -> str:
        pass

    @abstractmethod
    def generate_change_plan(self, query: str, context: str) -> str:
        pass

    @abstractmethod
    def generate_agent(self, intent: str, query: str, context: str) -> str:
        pass


class AbstractPromptMixin:
    """Provides the standard prompts and delegates strictly to _call(prompt, json_mode)."""
    
    def generate(self, question: str, context: str) -> str:
        prompt = (
            "Answer the user's question using the provided repository context.\n\n"
            f"Repository Context:\n{context}\n\n"
            f"User Question:\n{question}"
        )
        return self._call(prompt)

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
        return self._call(prompt, json_mode=True)

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

    @abstractmethod
    def _call(self, prompt: str, json_mode: bool = False) -> str:
        pass


class GroqProvider(AbstractPromptMixin, BaseLLMProvider):

    def __init__(self):
        settings = get_settings()
        api_key = settings.GROQ_API_KEY.strip()
        self.model = settings.GROQ_MODEL.strip()

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing or empty. "
                "Set it in the Render dashboard → Environment → GROQ_API_KEY."
            )

        self.client = Groq(
            api_key=api_key,
            timeout=Timeout(25.0, connect=5.0),
        )

    def _call(self, prompt: str, json_mode: bool = False) -> str:
        logger.info("LLM _call: sending request to Groq (model=%s)", self.model)
        try:
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1 if json_mode else 0.2,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            logger.info("LLM _call: response received (%d chars)", len(content))
            return content
        except Exception as e:
            e_str = str(e).lower()
            logger.error("LLM _call: Groq error - %s: %s", type(e).__name__, e)
            if "invalid_api_key" in e_str or "unauthorized" in e_str or "401" in e_str:
                raise ValueError("AI configuration error: Invalid API key") from None
            if "model" in e_str and ("not found" in e_str or "does not exist" in e_str):
                raise ValueError(f"AI configuration error: model '{self.model}' not found") from None
            if "timeout" in e_str or "timed out" in e_str:
                raise ValueError("AI service timed out") from None
            if "context_length" in e_str or "maximum context" in e_str or "too many tokens" in e_str:
                raise ValueError("AI service error: prompt too long") from None
            raise ValueError(f"AI service unavailable: {type(e).__name__}: {str(e)[:200]}") from None


class GeminiProvider(AbstractPromptMixin, BaseLLMProvider):

    def __init__(self):
        settings = get_settings()
        api_key = settings.GEMINI_API_KEY.strip()
        self.model_name = settings.GEMINI_MODEL.strip()

        if not api_key:
            raise ValueError("Gemini is not configured")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _call(self, prompt: str, json_mode: bool = False) -> str:
        logger.info("LLM _call: sending request to Gemini (model=%s)", self.model_name)
        try:
            generation_config = genai.GenerationConfig(temperature=0.1 if json_mode else 0.2)
            if json_mode:
                generation_config.response_mime_type = "application/json"
            
            full_prompt = _SYSTEM_PROMPT + "\n\n" + prompt
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            content = response.text or ""
            logger.info("LLM _call: response received (%d chars)", len(content))
            return content
        except Exception as e:
            logger.error("LLM _call: Gemini error - %s: %s", type(e).__name__, e)
            raise ValueError("Gemini is currently unavailable.") from None


def LLMService(provider: str = "devos_auto") -> BaseLLMProvider:
    settings = get_settings()
    has_groq = bool(settings.GROQ_API_KEY.strip())
    has_gemini = bool(settings.GEMINI_API_KEY.strip())

    if provider == "devos_auto":
        # In DEVOS_AUTO mode, we prefer Gemini if available, fallback to Groq
        if has_gemini:
            try:
                return GeminiProvider()
            except Exception:
                if has_groq:
                    logger.warning("Gemini unavailable — DevOs switched to Groq.")
                    return GroqProvider()
                raise
        elif has_groq:
            return GroqProvider()
        else:
            raise ValueError("No AI providers configured in DevOs Auto.")

    elif provider == "gemini":
        return GeminiProvider()
        
    elif provider == "groq":
        return GroqProvider()
        
    else:
        # Default fallback
        if has_groq:
            return GroqProvider()
        elif has_gemini:
            return GeminiProvider()
        else:
            raise ValueError(f"Unknown provider '{provider}' and no valid fallbacks available.")