# core/llm_config.py

from langchain_community.chat_models import ChatOpenAI, ChatAnthropic

# === Fallback to local config overrides ===
try:
    from llm_config_local import PRIMARY_MODEL_KEY, SECONDARY_MODEL_KEY, POWER_MODEL_KEY
except ImportError:
    PRIMARY_MODEL_KEY = "gpt-4.1-mini"
    SECONDARY_MODEL_KEY = "gpt-4.1-nano"
    POWER_MODEL_KEY = "gpt-4.1"

# === Shared LLM settings ===
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1024

# === Instantiate Models ===
GPT_4_1 = ChatOpenAI(model_name="gpt-4.1", temperature=DEFAULT_TEMPERATURE, max_tokens=2048)
GPT_4_1_NANO = ChatOpenAI(model_name="gpt-4.1-nano", temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)
GPT_4_1_MINI = ChatOpenAI(model_name="gpt-4.1-mini", temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)
# CLAUDE_SONNET = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=DEFAULT_TEMPERATURE, max_tokens=2048)

# === All available models ===
MODELS = {
    "gpt-4.1": GPT_4_1,
    "gpt-4.1-nano": GPT_4_1_NANO,
    "gpt-4.1-mini": GPT_4_1_MINI,
    # "claude": CLAUDE_SONNET,
}

# === Assigned Models Based on Config Keys ===
PRIMARY_MODEL = MODELS.get(PRIMARY_MODEL_KEY) # default
SECONDARY_MODEL = MODELS.get(SECONDARY_MODEL_KEY) # less powerful
POWER_MODEL = MODELS.get(POWER_MODEL_KEY) # full powaaa

# === Model Retrieval Function ===
def get_llm(name: str = "primary"):
    model = {
        "primary": PRIMARY_MODEL,
        "secondary": SECONDARY_MODEL,
        "power": POWER_MODEL,
        "nano": GPT_4_1_NANO,
        "mini": GPT_4_1_MINI,
        "gpt-4.1": GPT_4_1,
        # "claude": CLAUDE_SONNET,
    }.get(name, PRIMARY_MODEL)

    if not model:
        raise ValueError(f"❌ LLM key '{name}' is not a valid model key.")
    
    # ✅ Print the actual model name used
    #print(f"🧠 [LLM CONFIG] Using model key: '{name}' → model_name: '{model.model_name}'")
    
    return model
