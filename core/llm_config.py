# core/llm_config.py

from crewai import LLM
from langchain_anthropic import ChatAnthropic

# === Fallback to local config overrides ===
try:
    from llm_config_local import PRIMARY_MODEL_KEY, SECONDARY_MODEL_KEY, POWER_MODEL_KEY, CODING_MODEL_KEY
except ImportError:
    PRIMARY_MODEL_KEY = "gpt-4.1-mini"
    SECONDARY_MODEL_KEY = "gpt-4.1-nano"
    POWER_MODEL_KEY = "gpt-4.1"
    CODING_MODEL_KEY = "gpt-4.1"

# === Shared LLM settings ===
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1024

# === Instantiate Models ===
GPT_4_1 = LLM(model="gpt-4.1", temperature=DEFAULT_TEMPERATURE, max_tokens=2048)
GPT_4_1_NANO = LLM(model="gpt-4.1-nano", temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)
GPT_4_1_MINI = LLM(model="gpt-4.1-mini", temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)

# Claude models - using correct model identifiers
CLAUDE_SONNET = ChatAnthropic(
    model="claude-3-5-sonnet-20240620",
    temperature=DEFAULT_TEMPERATURE,
    max_tokens=2048
)

# Test the model with a simple query
#test_response = CLAUDE_SONNET.invoke("Hello, are you working?")
#print(f"Claude test response: {test_response}")

# === All available models ===
MODELS = {
    "gpt-4.1": GPT_4_1,
    "gpt-4.1-nano": GPT_4_1_NANO,
    "gpt-4.1-mini": GPT_4_1_MINI,
    "claude": CLAUDE_SONNET
}

# === Assigned Models Based on Config Keys ===
PRIMARY_MODEL = MODELS.get(PRIMARY_MODEL_KEY, GPT_4_1_MINI)  # Added fallback
SECONDARY_MODEL = MODELS.get(SECONDARY_MODEL_KEY, GPT_4_1_NANO)  # Added fallback
POWER_MODEL = MODELS.get(POWER_MODEL_KEY, GPT_4_1)  # Added fallback
CODING_MODEL = MODELS.get(CODING_MODEL_KEY, GPT_4_1)  # Added fallback

# === Model Retrieval Function ===
def get_llm(name: str = "primary"):
    model = {
        "primary": PRIMARY_MODEL,
        "secondary": SECONDARY_MODEL,
        "power": POWER_MODEL,
        "coding": CODING_MODEL,
        "nano": GPT_4_1_NANO,
        "mini": GPT_4_1_MINI,
        "gpt-4.1": GPT_4_1,
        "claude": CLAUDE_SONNET
    }.get(name, PRIMARY_MODEL)

    try:
        if hasattr(model, "model"):
            model_name = model.model
        elif hasattr(model, "llm") and hasattr(model.llm, "model"):
            model_name = model.llm.model
        elif hasattr(model, "model_name"):
            model_name = model.model_name
        else:
            model_name = str(model)
    except Exception as e:
        model_name = f"Unknown (error: {str(e)})"
    
    # ✅ Print the actual model name used
    print(f"🧠 [LLM CONFIG] Using model key: '{name}' → model_name: '{model_name}'")
    
    return model