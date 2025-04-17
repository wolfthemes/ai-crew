
import streamlit as st
import requests
import threading
import os
import json
import html
import html2text
import subprocess
from html import unescape
from crews.support_crew import support_crew_with_research
from tools import preprocess_tickets
from utils.helpers import time_ago, strip_html_tags
from utils.post_to_ticksy import post_to_ticksy
from utils.tinymce_component import tinymce_editor, get_tinymce_content, delete_tinymce_draft
from uvicorn import Config, Server
from utils.editor_api import app  # your FastAPI app

def run_fastapi():
    config = Config(app=app, port=5050, log_level="info")
    server = Server(config)
    server.run()

# Run only once
if "fastapi_started" not in st.session_state:
    threading.Thread(target=run_fastapi, daemon=True).start()
    st.session_state.fastapi_started = True

if "preprocessing_done" not in st.session_state:
    preprocess_tickets.run_preprocessing()
    st.session_state.preprocessing_done = True

# Load preprocessed tickets
with open("data/dynamic/tickets/preprocessed_tickets.json", encoding="utf-8") as f:
    tickets_data = json.load(f)["preprocessed_tickets"]

st.set_page_config(page_title="WolfThemes Tickets", layout="wide")
st.title("🛠️ Ticket Dashboard")

# Sidebar: ticket list
st.sidebar.header("📬 Tickets")

if not tickets_data:
    st.sidebar.markdown("🎉 No ticket left to process!", unsafe_allow_html=True)
else:
    for idx, ticket in enumerate(tickets_data):
        summary_clean = strip_html_tags(ticket['full_thread_sumary'])
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

st.sidebar.divider()

if st.sidebar.button("🔄 Refresh Tickets"):
    with st.spinner("Refreshing ticket data..."):
        preprocess_tickets.run_preprocessing()
        st.session_state.preprocessing_done = True
        st.success("✅ Ticket data refreshed!")
        st.rerun()

cols = st.columns([2, 1])

# === LEFT: Ticket content ===
if not tickets_data:
    st.markdown("No ticket.", unsafe_allow_html=True)
else:
    # Main panel: show selected ticket
    selected_idx = st.session_state.get("selected_ticket", 0)
    if not tickets_data:
        st.markdown("❌ No tickets available.", unsafe_allow_html=True)
    elif selected_idx is None or selected_idx >= len(tickets_data):
        st.markdown("ℹ️ No ticket selected.", unsafe_allow_html=True)
    else:
        with cols[0]:
            ticket = tickets_data[selected_idx]
            # Only show discussion if there's more than one message
            if len(ticket["full_thread"]) > 1:
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

                        # ⬇️ Display attachments if present
                        # TODO display attachemnt

                        st.markdown(f"**[{role}] {name}** — *{timestamp}*", unsafe_allow_html=True)
                        st.markdown(comment_html, unsafe_allow_html=True)
                        st.markdown("---")

            
            single_summary_clean = strip_html_tags(ticket['full_thread_sumary'])
            st.subheader(f"🗨️ {single_summary_clean}")
            st.markdown(html.unescape(ticket["last_message"]), unsafe_allow_html=True)

            # ⬇️ Display attachments if present
            # TODO display attachemnt

            st.divider()

            ticket_id = ticket["id"]
            editor_state_key = f"editor_reply_{ticket_id}"
            initial_content = ""

            # TODO: store the editor history in session
            # st.session_state[f"{ticket_id}_history"] = {
            #     "original": ...,
            #     "generated": ...,
            #     "reformulated": ...,
            # }
            
            crew_instruction = st.text_area("📝 Paste an optional note here:")
            if st.button("🤖 Generate / Regenerate Reply"):
                with st.spinner("Generating reply..."):
                    try:
                        
                        result = support_crew_with_research(ticket["last_message"], instruction=crew_instruction, ticket_id=ticket_id)
                        reply_html = result["reply"].output if hasattr(result["reply"], "output") else str(result["reply"])
                        st.session_state[editor_state_key] = reply_html
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error running agent: {str(e)}")


            st.subheader("✍️ Edit and Post Reply (HTML)")

            # Load latest draft, fallback to get_tinymce_content
            initial_content = st.session_state.get(editor_state_key, get_tinymce_content(ticket_id))
            tinymce_editor(initial_content=initial_content, ticket_id=ticket_id, height=450)
            
            col1, col2 = st.columns(2)

            from utils.ticket_utils import reformulate_reply

            st.markdown("### ✏️ Reformulate Reply")
            reformulate_instruction = st.text_area("Optional reformulation")
            
            if st.button("♻️ Reformulate"):
                try:
                    current_reply = get_tinymce_content(ticket_id)
                    if not current_reply.strip():
                        st.warning("⚠️ Editor is empty.")
                    else:
                        reformulated = reformulate_reply(
                            reply_text=current_reply,
                            instruction=reformulate_instruction,
                            last_user_message=ticket["last_message"]
                        )
                        st.session_state[editor_state_key] = reformulated
                        st.rerun()
                except Exception as e:
                    st.error(f"Reformulation error: {str(e)}")


            st.divider()

            col1, col2 = st.columns([1, 2])

            with col1:
                #private_reply = st.checkbox("Private", value=False)
                close_ticket = st.checkbox("Close Ticket", value=False)

            with col2:

                if st.button("✅ Post Reply to Ticksy"):
                    
                    current_reply = get_tinymce_content(ticket_id)
                    if not current_reply.strip():
                        st.warning("⚠️ Editor is empty — nothing to post.")
                    else:
                        result = post_to_ticksy(ticket_id=ticket_id, message=current_reply, close_ticket=close_ticket)
                        if result.get("status") == "ok":
                            st.success("✅ Reply posted to Ticksy.")
                            if editor_state_key in st.session_state:
                                del st.session_state[editor_state_key]

                            delete_tinymce_draft(ticket_id)

                            st.rerun()
                        else:
                            st.error("❌ Failed to post. Check console/logs.")

        # === RIGHT: Ticket metadata ===
        with cols[1]:
            
            st.markdown("### 🧾 Ticket Info")
            st.markdown(f"**Theme:** {ticket['theme']}")
            st.markdown(f"**Customer:** [{ticket['customer']}]({ticket['customer_url']})")
            st.markdown(f"**Website:** {ticket['user_site']}")
            st.markdown(f"**Ticket Link:** [#{ticket['id']}]({ticket['ticket_url']})")
