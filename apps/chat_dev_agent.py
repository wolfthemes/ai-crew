# streamlit run apps/chat_dev_agent.py --server.runOnSave=true
from pathlib import Path
import sys
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
import json
import subprocess
from crewai import Task, Crew
from crews.dev_crew import dev_crew
from agents.dev.dev_agent import dev_agent
from tasks.dev.dev_task import dev_assistance_task
from dotenv import load_dotenv


load_dotenv()

REPO_ROOT = os.path.abspath("repos")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if "dev_context" not in st.session_state:
    st.session_state.dev_context = {
        "repo": None,
        "owner": GITHUB_USERNAME,
        "branch": None,
        "last_file": None,
        "last_function": None,
        "last_operation": None,
        "working_repos": [],  # List of repos the agent has worked with
        "recent_commits": [],  # Track recent commit operations
        "safety_mode": True   # Enable AI branch safety by default
    }

st.set_page_config(page_title="Dev Agent Chat", layout="wide")

st.sidebar.title("📂 Codebase Context")

# Repository selection
repos_dir = "repos"
code_extensions = (".py", ".php", ".js", ".ts", ".css", ".html")

# List repos + default "All Repos" option
repo_options = ["-- All Repos --"] + sorted([
    d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d))
])
selected_repo = st.sidebar.selectbox("Select a repo", repo_options)

# Update context when repo changes
if selected_repo != "-- All Repos --" and selected_repo != st.session_state.dev_context.get("repo"):
    st.session_state.dev_context["repo"] = selected_repo
    
    # Get current branch for the selected repo
    try:
        repo_path = os.path.join(REPO_ROOT, selected_repo)
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        current_branch = result.stdout.strip()
        st.session_state.dev_context["branch"] = current_branch
    except Exception:
        st.session_state.dev_context["branch"] = "unknown"

# Display and select branch
if selected_repo != "-- All Repos --":
    try:
        repo_path = os.path.join(REPO_ROOT, selected_repo)
        # Get all branches
        result = subprocess.run(
            ["git", "branch"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        branches = [b.strip().replace("* ", "") for b in result.stdout.split("\n") if b.strip()]
        current_branch = st.session_state.dev_context.get("branch", "unknown")
        selected_branch = st.sidebar.selectbox("Select branch", branches, 
            index=branches.index(current_branch) if current_branch in branches else 0
        )
        
        # Update context when branch changes
        if selected_branch != st.session_state.dev_context.get("branch"):
            st.session_state.dev_context["branch"] = selected_branch
            # Checkout the selected branch
            subprocess.run(
                ["git", "checkout", selected_branch],
                cwd=repo_path,
                check=True
            )
    except Exception as e:
        st.sidebar.error(f"Error fetching branches: {e}")

# File selection based on repository
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

# Safety mode toggle
safety_mode = st.sidebar.checkbox("AI branch safety mode", 
                                  value=st.session_state.dev_context.get("safety_mode", True),
                                  help="When enabled, write operations are restricted to branches with 'ai-' or '-ai' in their name")

# Update safety mode in context
st.session_state.dev_context["safety_mode"] = safety_mode

# Branch status indicator
current_branch = st.session_state.dev_context.get("branch")
if current_branch and selected_repo != "-- All Repos --":
    is_ai_branch = current_branch.startswith('ai-') or '-ai' in current_branch
    if safety_mode and not is_ai_branch:
        st.sidebar.warning(f"⚠️ Current branch '{current_branch}' is not an AI branch. Write operations will be restricted.")
    elif safety_mode and is_ai_branch:
        st.sidebar.success(f"✅ Current branch '{current_branch}' is an AI branch. All operations allowed.")
    elif not safety_mode:
        st.sidebar.info(f"ℹ️ Safety mode disabled. All operations allowed on branch '{current_branch}'.")

# Recent activity section
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Recent Activity")

# Show recent commits if any
if st.session_state.dev_context.get("recent_commits"):
    recent_commits = st.session_state.dev_context["recent_commits"][-5:]  # Show last 5
    for commit in recent_commits:
        st.sidebar.markdown(f"📝 **{commit['repo']}**: {commit['message'][:40]}...")

# Main chat interface
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

    # Try structured JSON input first - Note used
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
            f"Branch: {ctx['branch'] or 'unknown'}\n"
            f"Safety Mode: {'Enabled' if ctx['safety_mode'] else 'Disabled'}\n"
        )
        if ctx["last_file"]:
            context_injection += f"File: {ctx['last_file']}\n"
        if ctx["last_function"]:
            context_injection += f"Last function: {ctx['last_function']}\n"
        if ctx["working_repos"]:
            context_injection += f"Working repositories: {', '.join(ctx['working_repos'])}\n"

        task = dev_assistance_task(query=query, memory_context=memory_context, context_injection=context_injection)

        # task = Task(
        #     description=f"{memory_context}\nUser: {query}\n{context_injection}",
        #     agent=dev_agent,
        #     expected_output="A concise and actionable response to the developer question."
        # )

    #crew = Crew(agents=[dev_agent], tasks=[task])
    crew = dev_crew(task)
    result = crew.kickoff()

    # Display assistant response
    st.session_state.messages.append({"role": "assistant", "content": result})
    with st.chat_message("assistant"):
        st.markdown(result)
        
    # Update working repos list if not already there
    if selected_repo != "-- All Repos --" and selected_repo not in st.session_state.dev_context["working_repos"]:
        st.session_state.dev_context["working_repos"].append(selected_repo)