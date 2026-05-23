# pyrefly: ignore [missing-import]
from groq import Groq

try:
    from config import GROQ_API_KEY, AI_MODEL, AI_TEMPERATURE, AI_MAX_TOKENS, SYSTEM_PROMPT
except ImportError:
    from src.config import GROQ_API_KEY, AI_MODEL, AI_TEMPERATURE, AI_MAX_TOKENS, SYSTEM_PROMPT

# Lazy-initialized client — only created on first use after key validation
_client = None


def _get_client():
    """Get or create the Groq client, validating the API key first."""
    global _client
    if not GROQ_API_KEY:
        raise ValueError(
            "API key not found. Please set your GROQ_API_KEY in the .env file.\n"
            "Get a free key at: https://console.groq.com/keys"
        )
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def _build_messages(command, conversation_history):
    """Build the messages list for the Groq chat completion API."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in conversation_history:
        messages.append({"role": "user", "content": msg.get("user_command", "")})
        messages.append({"role": "assistant", "content": msg.get("assistant_response", "")})

    messages.append({"role": "user", "content": command})
    return messages


def aiprocess(command, conversation_history=None):
    """Process a command through Groq with optional conversation context."""
    try:
        client = _get_client()
    except ValueError as e:
        return str(e)

    try:
        history = conversation_history[-10:] if conversation_history else []
        messages = _build_messages(command, history)

        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        error_str = str(e).lower()
        if "api_key" in error_str or "invalid" in error_str or "unauthorized" in error_str or "401" in error_str:
            return "Invalid API key. Please update your GROQ_API_KEY in the .env file."
        elif "quota" in error_str or "rate" in error_str or "429" in error_str:
            return "Rate limit reached. Please wait a moment and try again."
        elif "safety" in error_str:
            return "The response was blocked by safety filters. Please try rephrasing your question."
        else:
            return f"Sorry, there was an error processing your request: {str(e)}"


def aiprocess_stream(command, conversation_history=None):
    """Stream AI response chunks via a generator for SSE."""
    try:
        client = _get_client()
    except ValueError as e:
        yield str(e)
        return

    try:
        history = conversation_history[-10:] if conversation_history else []
        messages = _build_messages(command, history)

        stream = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    except Exception as e:
        error_str = str(e).lower()
        if "api_key" in error_str or "invalid" in error_str or "unauthorized" in error_str or "401" in error_str:
            yield "Invalid API key. Please update your GROQ_API_KEY in the .env file."
        elif "quota" in error_str or "rate" in error_str or "429" in error_str:
            yield "Rate limit reached. Please wait a moment and try again."
        elif "safety" in error_str:
            yield "The response was blocked by safety filters. Please try rephrasing."
        else:
            yield f"Sorry, there was an error: {str(e)}"
