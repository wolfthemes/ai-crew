# llm_config.py

from langchain.chat_models import ChatOpenAI
from langchain.chat_models import ChatAnthropic

# === Model Setup ===
max_tokens = 1024
temperature = 0.2

# Main lightweight models (cheap, fast)
GPT_4O_MINI = ChatOpenAI(model_name="gpt-4o", temperature=temperature, max_tokens=max_tokens)
GPT_4_1_NANO = ChatOpenAI(model_name="gpt-4-1-nano", temperature=temperature, max_tokens=max_tokens)

# Fallback stronger models (for hard tasks or review failures)
GPT_4_TURBO = ChatOpenAI(model_name="gpt-4-turbo", temperature=temperature, max_tokens=max_tokens)
#CLAUDE_SONNET = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=temperature, max_tokens=max_tokens)

# === Configurable default setup ===

# You can switch these based on your use case
PRIMARY_MODEL = GPT_4O_MINI
FALLBACK_MODEL = GPT_4_TURBO

# Optional dynamic access function
def get_llm(name: str = "primary"):
    if name == "primary":
        return PRIMARY_MODEL
    elif name == "fallback":
        return FALLBACK_MODEL
    elif name == "nano":
        return GPT_4_1_NANO
    elif name == "gpt4o":
        return GPT_4O_MINI
    elif name == "turbo":
        return GPT_4_TURBO
    #elif name == "claude":
        #return CLAUDE_SONNET
    else:
        raise ValueError(f"Unknown model key: {name}")
