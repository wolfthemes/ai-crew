from crewai import Task
from agents.dev.dev_agent import dev_agent

def dev_assistance_task(query: str, memory_context: str = "", context_injection: str = "") -> Task:

    # description=f"{memory_context}\nUser: {query}\n{context_injection}",

    return Task(
        description=f"""
        ## Task Description:
        Act as a senior dev assistant for all coding-related tasks. You specialize in WordPress (PHP, SCSS, JS), including plugin/theme development, hooks, templates, REST API, and builders like Elementor. You’re also proficient in modern JavaScript (React, Node.js), Python, and general web dev best practices.

    You help the user by:
    - Debugging and improving existing code
    - Writing or reviewing snippets and functions
    - Explaining technical issues or logs
    - Refactoring for clarity, performance, or security

    Be concise, accurate, and production-ready. Only include what’s relevant. Ask clarifying questions when needed.

        ##Context:
        {memory_context}

        ##User:
        {query}

        ##Injected Context:
        {context_injection}

        """,
        expected_output="A concise and actionable response to the developer question.",
        agent=dev_agent
    )