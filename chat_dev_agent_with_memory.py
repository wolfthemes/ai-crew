import streamlit as st
import os
import json
from crewai import Task, Crew
from agents.dev_agent import dev_agent
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = os.path.abspath("repos")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if "dev_context" not in st.session_state:
    st.session_state.dev_context = {
        "repo": None,
        "owner": GITHUB_USERNAME,
        "branch": "main",
        "last_file": None,
        "last_function": None,
        "last_operation": None,
        "working_repos": [],
        "recent_commits": []
    }

# 🔁 NEW: Memory depth selector
history_turns = st.sidebar.slider("🧠 Memory Depth (turns)", 1, 10, 3)

st.sidebar.title("📂 Codebase Context")

# ... [unchanged file/folder dropdowns] ...

# Show chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if query := st.chat_input("Ask your dev agent..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    try:
        user_input = json.loads(query)
        task = Task(
            description="Dev task using structured input.",
            agent=dev_agent,
            input=user_input,
            expected_output="Exact file and line of the matching function in the repo."
        )
    except json.JSONDecodeError:
        if selected_repo != "-- All Repos --":
            st.session_state.dev_context["repo"] = selected_repo
        if selected_file != "-- All Files --":
            st.session_state.dev_context["last_file"] = selected_file

        # 🔁 NEW: Inject chat memory dynamically
        memory_context = ""
        history = st.session_state.messages[-2 * history_turns:]
        for i in range(0, len(history), 2):
            try:
                user_msg = history[i]["content"]
                assistant_msg = history[i+1]["content"]
                memory_context += f"User: {user_msg}\\nAssistant: {assistant_msg}\\n"
            except IndexError:
                break

        ctx = st.session_state.dev_context
        context_injection = (
            f"\\n\\n[Context]\\n"
            f"Repo: {ctx['repo'] or 'unknown'}\\n"
            f"Branch: {ctx['branch']}\\n"
        )
        if ctx["last_file"]:
            context_injection += f"File: {ctx['last_file']}\\n"
        if ctx["last_function"]:
            context_injection += f"Last function: {ctx['last_function']}\\n"

        task = Task(
            description=f"{memory_context}\\nUser: {query}\\n{context_injection}",
            agent=dev_agent,
            expected_output="A concise and actionable response to the developer question."
        )

    crew = Crew(agents=[dev_agent], tasks=[task])
    result = crew.kickoff()

    st.session_state.messages.append({"role": "assistant", "content": result})
    with st.chat_message("assistant"):
        st.markdown(result)
