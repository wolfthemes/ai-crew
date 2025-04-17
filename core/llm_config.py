# core/llm_config.py

from langchain_community.chat_models import ChatOpenAI, ChatAnthropic

# === Model Setup ===
max_tokens = 1024
temperature = 0.2

GPT_4 = ChatOpenAI(model_name="gpt-4", temperature=temperature, max_tokens=max_tokens)
GPT_4O_MINI = ChatOpenAI(model_name="gpt-4o", temperature=temperature, max_tokens=max_tokens)
GPT_4_1_NANO = ChatOpenAI(model_name="gpt-4-1-nano", temperature=temperature, max_tokens=max_tokens)
GPT_4_TURBO = ChatOpenAI(model_name="gpt-4-turbo", temperature=temperature, max_tokens=2048)
#CLAUDE_SONNET = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=temperature, max_tokens=2048)

PRIMARY_MODEL = GPT_4
SECONDARY_MODEL = GPT_4O_MINI
FALLBACK_MODEL = GPT_4_TURBO

def get_llm(name: str = "primary"):
    return {
        "primary": PRIMARY_MODEL,
        "secondary": SECONDARY_MODEL,
        "fallback": FALLBACK_MODEL,
        "nano": GPT_4_1_NANO,
        "gpt4o": GPT_4O_MINI,
        "turbo": GPT_4_TURBO,
        #"claude": CLAUDE_SONNET,
    }.get(name)

