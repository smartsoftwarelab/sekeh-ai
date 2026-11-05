import requests
from config import Config


def chunk_text(text: str, chunk_size: int = 220):
    """برای SSE: چون stream واقعی نداریم، خروجی را تکه‌ای می‌کنیم."""
    text = text or ""
    if not text:
        return
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


def qom_chat(messages, temperature=None, max_tokens=None, timeout=None) -> str:
    """Call the configured OpenAI-compatible chat completions API."""
    if not Config.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is not set")

    if not Config.LLM_MODEL:
        raise RuntimeError("LLM_MODEL is not set")

    url = Config.llm_chat_url()
    if not url or url == "/chat/completions":
        raise RuntimeError("LLM chat URL is not configured")

    headers = {
        "Authorization": f"Bearer {Config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": Config.LLM_MODEL,
        "messages": messages,
        "temperature": Config.LLM_TEMPERATURE if temperature is None else temperature,
        "max_tokens": Config.LLM_MAX_TOKENS if max_tokens is None else max_tokens,
        "stream": False,
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=Config.LLM_TIMEOUT if timeout is None else timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("LLM response has an invalid chat completion shape") from exc

    if not isinstance(content, str):
        raise RuntimeError("LLM response content is not text")

    return content.strip()