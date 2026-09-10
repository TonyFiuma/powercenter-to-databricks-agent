import os

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


load_dotenv()


def create_llm(
    provider: str,
    model: str,
):
    """
    Create an LLM instance based on the configured provider.

    Supported providers:
    - groq
    - openrouter
    - openai
    - ollama
    """

    provider = provider.lower()

    # ==================================================
    # Groq
    # ==================================================

    if provider == "groq":
        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        return ChatGroq(
            model=model,
            api_key=api_key,
            temperature=0,
        )

    # ==================================================
    # OpenRouter
    # ==================================================

    if provider == "openrouter":
        api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not configured."
            )

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=(
                "https://openrouter.ai/api/v1"
            ),
            temperature=0,
            timeout=90,
            max_retries=1,
        )

    # ==================================================
    # OpenAI
    # ==================================================

    if provider == "openai":
        api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured."
            )

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0,
        )

    # ==================================================
    # Ollama
    # ==================================================

    if provider == "ollama":
        return ChatOllama(
            model=model,
            temperature=0,
        )

    # ==================================================
    # Unsupported provider
    # ==================================================

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )


def get_planner_llm():
    """
    Return the LLM configured for migration planning.
    """

    provider = os.getenv(
        "PLANNER_LLM_PROVIDER",
        "groq",
    )

    model = os.getenv(
        "PLANNER_LLM_MODEL",
        "openai/gpt-oss-120b",
    )

    print(
        f"Planner LLM: "
        f"{provider} / {model}"
    )

    return create_llm(
        provider=provider,
        model=model,
    )


def get_generator_llm():
    """
    Return the LLM configured for PySpark generation.
    """

    provider = os.getenv(
        "GENERATOR_LLM_PROVIDER",
        "groq",
    )

    model = os.getenv(
        "GENERATOR_LLM_MODEL",
        "openai/gpt-oss-120b",
    )

    print(
        f"Generator LLM: "
        f"{provider} / {model}"
    )

    return create_llm(
        provider=provider,
        model=model,
    )