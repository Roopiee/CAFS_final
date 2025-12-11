import os
from typing import Optional


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:

    CSV_PATH = os.path.join(BASE_DIR, "data/onlinelist.csv")
    LOG_LEVEL = "INFO"

    """
    Configuration management for the multiagent forgery detection system.
    """
    
    # LLM Configuration
    LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "true").lower() == "true"
    LLM_MODEL: str = os.getenv("LLM_MODEL", "mistral")  # Default Ollama model
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))  # seconds
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))  # Low temp for consistent analysis
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "500"))
    
    # Ollama Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # File Paths
    CSV_PATH: str = os.getenv("CSV_PATH", "onlinelist.csv")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """Returns LLM configuration as a dictionary."""
        return {
            "enabled": cls.LLM_ENABLED,
            "model": cls.LLM_MODEL,
            "timeout": cls.LLM_TIMEOUT,
            "temperature": cls.LLM_TEMPERATURE,
            "max_tokens": cls.LLM_MAX_TOKENS,
            "ollama_host": cls.OLLAMA_HOST
        }

config = Config()
