import os
from dotenv import load_dotenv

load_dotenv()

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Memory store paths
PROFILE_PATH = "profile.json"
EPISODES_PATH = "episodes.json"
SEMANTIC_PATH = "semantic_index"
