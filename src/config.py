import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this config file
_env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=_env_path)

# AI Configuration (Groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "1024"))

SYSTEM_PROMPT = (
    "You are Iris, a smart and friendly AI assistant. "
    "You are skilled at answering questions, helping with tasks, writing code, "
    "doing math, and having natural conversations. "
    "Format your responses using Markdown when appropriate (headings, bold, "
    "code blocks, lists). Be concise but thorough."
)

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "iris_assistant")
