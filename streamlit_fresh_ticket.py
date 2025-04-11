# streamlit run streamlit_fresh_ticket.py

import streamlit as st
from crewai import Crew
from tasks.task_fresh_ticket import support_task_fresh  # this task uses support_agent
from crews.support_crew import support_crew_fresh_with_review
from utils.ticket_classifier import classify_ticket

st.set_page_config(page_title="WolfThemes Support Agent", layout="centered")

st.title("🧠 WolfThemes Support Assistant")

st.markdown("Paste a ticket message below. The agent will suggest a reply:")

ticket_input = st.text_area("🎫 Paste the customer ticket text here:", height=200)

if st.button("✉️ Generate Reply") and ticket_input.strip():
    # Update the task description
    support_task_fresh.description = f"""
You are responding to this customer support ticket:

"{ticket_input.strip()}"

Respond as helpfully and concisely as possible using the knowledge base and rules.
Your answer must be markdown formatted, short and professional.
"""

    # Run the agent via Crew wrapper
    # support_crew = Crew(
    #     agents=[support_task_fresh.agent],
    #     tasks=[support_task_fresh],
    #     verbose=False
    # )

    # 1. Classify the ticket for internal use
    category = classify_ticket(ticket_input)
    print(f"📋 Ticket classified as: {category}")
    
    # 3. Run both reply and review with proper crew
    print("🤖 Starting support crew...")

    result = support_crew_fresh_with_review(ticket_input)
    
    st.markdown("### 💬 Suggested Reply:")
    st.markdown(result["reply"])

    st.markdown("### 🕵️‍♂️ Quality Review:")
    st.markdown(result["review"])

elif st.button("❌ Clear"):
    ticket_input = ""
