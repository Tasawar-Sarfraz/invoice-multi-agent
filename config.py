
import os

from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not configured.")

groq_llm = LLM(
    model="openai/gpt-oss-20b",
    custom_openai=True,
    api_key=GROQ_API_KEY,
)
print("MODEL CHECK:", groq_llm.model)
