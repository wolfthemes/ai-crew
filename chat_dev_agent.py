import streamlit as st
import os
import json
from crewai import Task, Crew
from agents.dev_agent import dev_agent  # from your code
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
        "working_repos": [],  # List of repos the agent has worked with
        "recent_commits": []  # Track recent commit operations
    }


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

        # Inject context memory
        ctx = st.session_state.dev_context
        context_injection = (
            f"[Context]"
            #f"Repo: {ctx['owner']}/{ctx['repo'] or 'unknown'}"
            f"Repo: {ctx['repo'] or 'unknown'}"
            f"Branch: {ctx['branch']}"
        )
        if ctx["last_file"]:
            context_injection += f"File: {ctx['last_file']}"
        if ctx["last_function"]:
            context_injection += f"Last function: {ctx['last_function']}"

        task = Task(
            description=f"{query}{context_injection}",
            agent=dev_agent,
            expected_output="A concise and actionable response to the developer question."
        )

    crew = Crew(agents=[dev_agent], tasks=[task])
    result = crew.kickoff()

    # Display assistant response
    st.session_state.messages.append({"role": "assistant", "content": result})
    with st.chat_message("assistant"):
        st.markdown(result)
