# core/llm_config.py

from langchain_community.chat_models import ChatOpenAI, ChatAnthropic

# === Fallback to local config overrides ===
try:
    from llm_config_local import PRIMARY_KEY, SECONDARY_KEY, FALLBACK_KEY
except ImportError:
    PRIMARY_KEY = "gpt-4-1-nano"
    SECONDARY_KEY = "gpt-4o"
    FALLBACK_KEY = "gpt-4-turbo"

# === Shared LLM settings ===
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1024

# === Instantiate Models ===
GPT_4 = ChatOpenAI(model_name="gpt-4", temperature=DEFAULT_TEMPERATURE, max_tokens=2048)
GPT_4O = ChatOpenAI(model_name="gpt-4o", temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)
GPT_4_1_NANO = ChatOpenAI(model_name="gpt-4-1-nano", temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)
GPT_4_TURBO = ChatOpenAI(model_name="gpt-4-turbo", temperature=DEFAULT_TEMPERATURE, max_tokens=2048)
# CLAUDE_SONNET = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=DEFAULT_TEMPERATURE, max_tokens=2048)

# === All available models ===
MODELS = {
    "gpt-4": GPT_4,
    "gpt4o": GPT_4O,
    "gpt-4o": GPT_4O,
    "gpt-4-1-nano": GPT_4_1_NANO,
    "gpt-4-turbo": GPT_4_TURBO,
    # "claude": CLAUDE_SONNET,
}

# === Assigned Models Based on Config Keys ===
PRIMARY_MODEL = MODELS.get(PRIMARY_KEY)
SECONDARY_MODEL = MODELS.get(SECONDARY_KEY)
FALLBACK_MODEL = MODELS.get(FALLBACK_KEY)

# === Model Retrieval Function ===
def get_llm(name: str = "primary"):
    return {
        "primary": PRIMARY_MODEL,
        "secondary": SECONDARY_MODEL,
        "fallback": FALLBACK_MODEL,
        "nano": GPT_4_1_NANO,
        "gpt4o": GPT_4O,
        "turbo": GPT_4_TURBO,
        # "claude": CLAUDE_SONNET,
    }.get(name, PRIMARY_MODEL)
