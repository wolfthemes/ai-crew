
import streamlit as st
import requests
import os
import json
import html
import html2text
import subprocess
from html import unescape
from dotenv import load_dotenv
from crews.support_crew import support_crew_with_research
from utils.helpers import time_ago, strip_html_tags
from utils.tinymce_component import tinymce_editor, get_tinymce_content, submit_button_script_inline

if "api_started" not in st.session_state:
    subprocess.Popen(["uvicorn", "utils.editor_api:app", "--port", "5050", "--reload"])
    st.session_state.api_started = True

load_dotenv()
TINYMCE_API_KEY = os.getenv("TINYMCE_API_KEY")
TICKSY_DOMAIN = os.getenv("TICKSY_DOMAIN")
TICKSY_API_KEY = os.getenv("TICKSY_API_KEY")
TICKSY_API_URL = f"https://api.ticksy.com/v1/{TICKSY_DOMAIN}/{TICKSY_API_KEY}"

# Load preprocessed tickets
with open("data/dynamic/preprocessed_tickets.json", encoding="utf-8") as f:
    tickets_data = json.load(f)["preprocessed_tickets"]

st.set_page_config(page_title="WolfThemes Tickets", layout="wide")
st.title("🛠️ Ticket Dashboard")

# Sidebar: ticket list
st.sidebar.header("📬 Tickets")

for idx, ticket in enumerate(tickets_data):
    summary_clean = strip_html_tags(ticket['summary'])
    last_message_summary_clean = strip_html_tags(ticket['last_message_summary'])
    timestamp = time_ago(ticket.get("last_message_timestamp", "2025-01-01 00:00:00"))

    st.sidebar.markdown(f"""
    <div style='text-align: left; padding-bottom: 0.2em;'>
        {"🔒 " if ticket["needs_human"] else ""}<strong>{summary_clean}</strong><br>
        <span>{last_message_summary_clean}</span><br>
        <small>{ticket['customer']} ({ticket['theme']}) · {timestamp}</small><br>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("View ticket 🡺", key=f"ticket_{ticket['id']}"):
        st.session_state.selected_ticket = idx

# Main panel: show selected ticket
selected_idx = st.session_state.get("selected_ticket", 0)
ticket = tickets_data[selected_idx]

cols = st.columns([2, 1])

# === LEFT: Ticket content ===
with cols[0]:
   
    with st.expander("📜 Show Full Discussion"):
        comments = ticket["full_thread"]

        # Remove last message (already shown separately)
        comments = comments[1:]

        # Remove what was originally the last (now first) before reversing
        if comments:
            comments = list(reversed(comments))    # reverse to get oldest first

        for c in comments:
            name = c["commenter_name"]
            role = "User" if c["user_type"] == "user" else "Support"
            timestamp = c.get("time_stamp", "")
            comment_html = unescape(c["comment"])

            st.markdown(f"**[{role}] {name}** — *{timestamp}*", unsafe_allow_html=True)
            st.markdown(comment_html, unsafe_allow_html=True)
            st.markdown("---")

    single_summary_clean = strip_html_tags(ticket['summary'])
    st.subheader(f"🗨️ {single_summary_clean}")
    st.markdown(html.unescape(ticket["last_message"]), unsafe_allow_html=True)

    st.divider()
    
    crew_instruction = st.text_area("📝 Paste an optional note here:")

    if st.button("🤖 Generate / Regenerate Reply"):
        with st.spinner("Generating reply..."):
            try:
                result = support_crew_with_research(ticket["last_message"], instruction=crew_instruction)

                raw_reply = result["reply"].output if hasattr(result["reply"], "output") else str(result["reply"])
                markdown_debug = html2text.html2text(raw_reply)

                print("🧠 Crew Reply (Markdown View) →")
                print(markdown_debug)

                # ✅ Store to session
                st.session_state.generated_reply = result["reply"]
                st.session_state.reply = result["reply"]  # Ensure it's in the editor too
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error running agent: {str(e)}")


    st.subheader("✍️ Edit and Post Reply (HTML)")

    # Determine initial content
    initial_content = get_tinymce_content( ticket_id=ticket["id"] )
    if "reformulated_reply" in st.session_state:
        initial_content = st.session_state.reformulated_reply
        del st.session_state.reformulated_reply
    elif "generated_reply" in st.session_state:
        initial_content = st.session_state.generated_reply
        del st.session_state.generated_reply
    elif "reply" in st.session_state:
        initial_content = st.session_state.reply

    # Render TinyMCE with whatever is in session state
    tinymce_editor(initial_content=st.session_state.get("reply", ""), ticket_id=ticket["id"], height=450)
    reply = get_tinymce_content( ticket_id=ticket["id"] )
    
    st.markdown("### 🔁 Synced TinyMCE reply:")
    st.code(reply)
    
    #st.write(f"Retrieved from localStorage: {st.session_state.reply}")

    col1, col2 = st.columns(2)

    from utils.ticket_utils import reformulate_reply

    st.markdown("### ✏️ Reformulate Reply")
    reformulate_instruction = st.text_area("Optional reformulation")
    
    if st.button("♻️ Reformulate"):
        try:
            
            reply = get_tinymce_content( ticket_id=ticket["id"] )

            if not isinstance(reply, str):
                reply = str(reply)

            reformulated = reformulate_reply(
                reply_text=reply,
                instruction=reformulate_instruction,
                last_user_message=ticket["last_message"]
            )
            st.session_state.reformulated_reply = reformulated
            st.rerun()
        except Exception as e:
            st.error(f"Reformulation error: {str(e)}")


    st.divider()

    col1, col2 = st.columns([1, 2])

    with col1:
        private_reply = st.checkbox("Private", value=False)

    with col2:   

        st.markdown("""
        <button id="post_submit" style="padding: 0.5em 1em; font-size: 1em; background-color: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer;">
        ✅ Post Reply
        </button>
        """, unsafe_allow_html=True)
        submit_button_script_inline(ticket_id=ticket["id"], private=private_reply)

# === RIGHT: Ticket metadata ===
with cols[1]:
    
    st.markdown("### 🧾 Ticket Info")
    st.markdown(f"**Theme:** {ticket['theme']}")
    st.markdown(f"**Customer:** [{ticket['customer']}]({ticket['customer_url']})")
    st.markdown(f"**Website:** {ticket['user_site']}")
    st.markdown(f"**Ticket Link:** [View on Ticksy]({ticket['ticket_url']})")
