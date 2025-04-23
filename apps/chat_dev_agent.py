# streamlit run apps/chat_dev_agent.py --server.runOnSave=true
from pathlib import Path
import sys
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
import json
from crewai import Task, Crew
from agents.dev.dev_agent import dev_agent  # from your code
from dotenv import load_dotenv


load_dotenv()

REPO_ROOT = os.path.abspath("repos")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if "dev_context" not in st.session_state:
    st.session_state.dev_context = {
        "repo": None,
        "owner": GITHUB_USERNAME,
        "branch": "dev-ai",
        "last_file": None,
        "last_function": None,
        "last_operation": None,
        "working_repos": [],  # List of repos the agent has worked with
        "recent_commits": []  # Track recent commit operations
    }

st.set_page_config(page_title="Dev Agent Chat", layout="wide")

st.sidebar.title("📂 Codebase Context")

repos_dir = "repos"
code_extensions = (".py", ".php", ".js", ".ts", ".css")

# List repos + default "All Repos" option
repo_options = ["-- All Repos --"] + sorted([
    d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d))
])
selected_repo = st.sidebar.selectbox("Select a repo", repo_options)

repo_files = []
if selected_repo != "-- All Repos --":
    selected_repo_path = os.path.join(repos_dir, selected_repo)
    for root, dirs, files in os.walk(selected_repo_path):
        for file in files:
            if file.endswith(code_extensions):
                rel_path = os.path.relpath(os.path.join(root, file), selected_repo_path)
                repo_files.append(rel_path)

# Add default "All Files" option
file_options = ["-- All Files --"] + sorted(repo_files)
selected_file = st.sidebar.selectbox("Select a file", file_options)

st.title("💻 Dev Agent Chat")

history_turns = 20

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if query := st.chat_input("Ask your dev agent..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Try structured JSON input first
    try:
        user_input = json.loads(query)
        task = Task(
            description="Dev task using structured input.",
            agent=dev_agent,
            input=user_input,
            expected_output="Exact file and line of the matching function in the repo."
        )
    except json.JSONDecodeError:

        # Update memory from UI selections
        if selected_repo != "-- All Repos --":
            st.session_state.dev_context["repo"] = selected_repo
        if selected_file != "-- All Files --":
            st.session_state.dev_context["last_file"] = selected_file

        # Inject memory first
        memory_context = ""
        history = st.session_state.messages[-2 * history_turns:]
        for i in range(0, len(history), 2):
            try:
                user_msg = history[i]["content"]
                assistant_msg = history[i+1]["content"]
                memory_context += f"User: {user_msg}\nAssistant: {assistant_msg}\n"
            except IndexError:
                break

        # Then inject static context (repo, file, etc.)
        ctx = st.session_state.dev_context
        context_injection = (
            f"\n\n[Context]\n"
            f"Repo: {ctx['repo'] or 'unknown'}\n"
            f"Branch: {ctx['branch']}\n"
        )
        if ctx["last_file"]:
            context_injection += f"File: {ctx['last_file']}\n"
        if ctx["last_function"]:
            context_injection += f"Last function: {ctx['last_function']}\n"

        task = Task(
            description=f"{memory_context}\nUser: {query}\n{context_injection}",
            agent=dev_agent,
            expected_output="A concise and actionable response to the developer question."
        )

    crew = Crew(agents=[dev_agent], tasks=[task])
    result = crew.kickoff()

    # Display assistant response
    st.session_state.messages.append({"role": "assistant", "content": result})
    with st.chat_message("assistant"):
        st.markdown(result)
