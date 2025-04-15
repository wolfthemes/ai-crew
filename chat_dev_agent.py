import streamlit as st
import json
from crewai import Task, Crew
from agents.dev_agent import dev_agent  # from your code
# Optional: import tools here if not auto-loaded by agent setup

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
        task = Task(
            description=query,
            agent=dev_agent,
            expected_output="A concise and actionable response to the developer question."
        )

    crew = Crew(agents=[dev_agent], tasks=[task])
    result = crew.kickoff()

    # Display assistant response
    st.session_state.messages.append({"role": "assistant", "content": result})
    with st.chat_message("assistant"):
        st.markdown(result)
