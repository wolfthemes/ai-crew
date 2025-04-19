# streamlit run streamlit_fresh_ticket.py

import streamlit as st
from crewai import Crew
from crews.support_crew import support_crew_with_research
from utils.ticket_classifier import classify_ticket
from utils.helpers import convert_html_to_plaintext_with_urls

st.set_page_config(page_title="WolfThemes Support Agent", layout="centered")

st.title("🧠 WolfThemes Support Assistant")

st.markdown("Paste a ticket message below. The agent will suggest a reply:")

ticket_input = st.text_area("🎫 Paste the customer ticket text here:", height=200)

crew_instruction = st.text_area("📝 Paste an optional note here:")

if st.button("✉️ Generate Reply") and ticket_input.strip():
   
    # 1. Classify the ticket for internal use
    category = classify_ticket(ticket_input)
    print(f"📋 Ticket classified as: {category}")
    
    # 3. Run both reply and review with proper crew
    print("🤖 Starting support crew...")

    result = support_crew_with_research(ticket_input, instruction=crew_instruction)

    #st.markdown("### 🔎 Search:")
    #st.markdown(result["research"])
    
    st.markdown("### 💬 Suggested Reply:")
    html_reply = result["reply"]  # Your raw HTML reply
    plain_text_reply = convert_html_to_plaintext_with_urls(html_reply)
    st.markdown(plain_text_reply)

    #st.markdown("### 🕵️‍♂️ Quality Review:")
    #st.markdown(result["review"])

elif st.button("❌ Clear"):
    ticket_input = ""
