import streamlit as st
import json
import html
import re
from streamlit_ace import st_ace

from crews.support_crew import support_crew_with_research
from utils.helpers import time_ago
from utils.ticket_classifier import classify_ticket
from utils.ticket_utils import reformulate_reply

# Load preprocessed tickets
with open("data/dynamic/preprocessed_tickets.json", encoding="utf-8") as f:
    tickets_data = json.load(f)["preprocessed_tickets"]

def strip_html_tags(text):
    return re.sub(r"<.*?>", "", html.unescape(text)).strip()

st.set_page_config(page_title="WolfThemes Tickets", layout="wide")
st.title("🛠️ Ticket Dashboard")

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

selected_idx = st.session_state.get("selected_ticket", 0)
ticket = tickets_data[selected_idx]
cols = st.columns([2, 1])

with cols[0]:
    with st.expander("📜 Show Full Discussion"):
        for msg in ticket["formatted_text_thread"]:
            st.markdown(html.unescape(msg), unsafe_allow_html=True)

    st.subheader("🗨️ Last Message")
    st.markdown(html.unescape(ticket["last_message"]), unsafe_allow_html=True)
    st.divider()

    crew_instruction = st.text_input("📝 Paste an optional note here:")

    if st.button("🤖 Generate / Regenerate Reply"):
        with st.spinner("Generating reply..."):
            try:
                result = support_crew_with_research(ticket["last_message"], instruction=crew_instruction)
                st.session_state.generated_reply = result["reply"]
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error running agent: {str(e)}")

    st.subheader("✍️ Edit and Post Reply (HTML)")

    if "reformulated_reply" in st.session_state:
        st.session_state.reply = st.session_state.reformulated_reply
        del st.session_state.reformulated_reply
    elif "generated_reply" in st.session_state:
        st.session_state.reply = st.session_state.generated_reply
        del st.session_state.generated_reply

    reply_value = st.session_state.get("reply", "")
    if not isinstance(reply_value, str):
        reply_value = ""

    html_reply = st_ace(
        value=reply_value,
        language="html",
        theme="chrome",
        height=300,
        key="reply_editor"
    )

    if html_reply and html_reply.strip() != reply_value.strip():
        st.session_state.reply = html_reply

    col1, col2 = st.columns(2)

    st.markdown("### ✏️ Reformulate Reply")
    reformulate_instruction = st.text_input("Reformulation instruction (optional)")

    if col1.button("♻️ Reformulate"):
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

    col2.button("✅ Post Reply")

with cols[1]:
    st.markdown("### 🧾 Ticket Info")
    st.markdown(f"**Theme:** {ticket['theme']}")
    st.markdown(f"**Customer:** [{ticket['customer']}]({ticket['customer_url']})")
    st.markdown(f"**Website:** {ticket['user_site']}")
    st.markdown(f"**Ticket Link:** [View on Ticksy]({ticket['ticket_url']})")
