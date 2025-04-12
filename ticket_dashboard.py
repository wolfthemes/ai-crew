
import streamlit as st
import json
import html
import re

from crews.support_crew import support_crew_with_research
from utils.helpers import time_ago
from utils.ticket_classifier import classify_ticket

# Load preprocessed tickets
with open("data/dynamic/preprocessed_tickets.json", encoding="utf-8") as f:
    tickets_data = json.load(f)["preprocessed_tickets"]

# Strip basic HTML tags for sidebar
def strip_html_tags(text):
    return re.sub(r"<.*?>", "", html.unescape(text)).strip()

st.set_page_config(page_title="WolfThemes Tickets", layout="wide")
st.title("🛠️ Ticket Dashboard")

# Sidebar: ticket list
st.sidebar.header("📬 Tickets")

for idx, ticket in enumerate(tickets_data):
    summary_clean = strip_html_tags(ticket['summary'])
    timestamp = time_ago(ticket.get("last_message_timestamp", "2025-01-01 00:00:00"))

    st.sidebar.markdown(f"""
    <div style='text-align: left; padding-bottom: 0.2em;'>
        {"🔒 " if ticket["needs_human"] else ""}<strong>{summary_clean}</strong><br>
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
        for msg in ticket["formatted_text_thread"]:
            clean_msg = html.unescape(msg)
            st.markdown(msg, unsafe_allow_html=True)

    st.subheader("🗨️ Last Message")

    st.markdown(html.unescape(ticket["last_message"]), unsafe_allow_html=True)

    st.divider()
    
    crew_instruction = st.text_input("📝 Paste an optional note here:")
    
    if st.button("🤖 Generate / Regenerate Reply"):
        input_text = ticket["last_message"]
        with st.spinner("Generating reply..."):
            try:
                result = support_crew_with_research(input_text, instruction=crew_instruction)

                # ✅ Debug print — see reply before assigning
                st.markdown("### 🧪 Raw Crew Reply Output")
                st.code(result["reply"], language="html")

                # ⛔ Comment this out temporarily to avoid crash
                # st.session_state.generated_reply = result["reply"]
                # st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error running agent: {str(e)}")


    st.subheader("✍️ Suggested Reply")

    if "reply" not in st.session_state or st.session_state.reply is None:
        st.session_state.reply = ""
    elif "reformulated_reply" in st.session_state:
        st.session_state.reply = st.session_state.reformulated_reply
        del st.session_state.reformulated_reply
    elif "generated_reply" in st.session_state:
        st.session_state.reply = st.session_state.generated_reply
        del st.session_state.generated_reply

    reply_value = st.session_state.get("reply")
    if not isinstance(reply_value, str):
        reply_value = ""

    ai_reply = st.text_area(
        "Reply",
        value=reply_value,
        height=200,
        key="reply",
        help="You can use basic HTML tags like <p>, <a>, <strong>..."
    )

    col1, col2 = st.columns(2)

    from utils.ticket_utils import reformulate_reply

    st.markdown("### ✏️ Reformulate Reply")
    reformulate_instruction = st.text_input("Optional reformulation")
    
    if st.button("♻️ Reformulate"):
        try:
            reformulated = reformulate_reply(
                reply_text=st.session_state.reply,
                instruction=reformulate_instruction,
                last_user_message=ticket["last_message"]
            )
            st.session_state.reformulated_reply = reformulated
            st.rerun()
        except Exception as e:
            st.error(f"Reformulation error: {str(e)}")


    st.divider()

    st.button("✅ Post Reply")

# === RIGHT: Ticket metadata ===
with cols[1]:
    
    st.markdown("### 🧾 Ticket Info")
    st.markdown(f"**Theme:** {ticket['theme']}")
    st.markdown(f"**Customer:** [{ticket['customer']}]({ticket['customer_url']})")
    st.markdown(f"**Website:** {ticket['user_site']}")
    st.markdown(f"**Ticket Link:** [View on Ticksy]({ticket['ticket_url']})")
