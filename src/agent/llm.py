from langchain_openai import ChatOpenAI
from src.config import LLAMACPP_HOST, LLM_MAX_TOKENS, LLM_MODEL_NAME, LLM_TEMPERATURE


def get_llm(temperature: float = LLM_TEMPERATURE) -> ChatOpenAI:
    """
    Return ChatOpenAI client pointed at local llama.cpp server.

    llama.cpp exposes an OpenAI-compatible /v1/chat/completions endpoint.

    Tool calling requires llama.cpp built with --jinja support and a model
    that supports function calling (Qwen3 does natively).
    """
    return ChatOpenAI(
        model=LLM_MODEL_NAME,
        base_url=f"{LLAMACPP_HOST}/v1",
        api_key="local",
        temperature=temperature,
        max_tokens=LLM_MAX_TOKENS,
    )
