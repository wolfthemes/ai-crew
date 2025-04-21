from pathlib import Path
import sys
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import requests
import threading
import json
import html
from html import unescape
from crews.support_crew import support_crew_with_research
from scripts import preprocess_open_tickets
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
    preprocess_open_tickets.run_preprocessing()
    st.session_state.preprocessing_done = True

# Load preprocessed tickets into session state if not already there
if "tickets_data" not in st.session_state:
    # Load preprocessed tickets
    with open("data/dynamic/tickets/open_tickets.json", encoding="utf-8") as f:
        st.session_state.tickets_data = json.load(f)["open_tickets"]

# Initialize all required session state variables
if "post_success" not in st.session_state:
    st.session_state.post_success = False
    
if "clear_instruction" not in st.session_state:
    st.session_state.clear_instruction = False

if "close_ticket_checkbox" not in st.session_state:
    st.session_state.close_ticket_checkbox = False

if "selected_ticket" not in st.session_state:
    st.session_state.selected_ticket = 0 if st.session_state.tickets_data else None

st.set_page_config(page_title="WolfThemes Tickets", layout="wide")
st.title("🛠️ Ticket Dashboard")

# Initialize text area values by checking flags from previous run
crew_instruction_key = "crew_instruction"
reformulate_instruction_key = "reformulate_instruction"

# Clear text areas if needed based on flags from previous run
if st.session_state.clear_instruction:
    st.session_state[crew_instruction_key] = ""
    st.session_state[reformulate_instruction_key] = ""
    st.session_state.close_ticket_checkbox = False  # Reset the checkbox
    st.session_state.clear_instruction = False  # Reset flag
    
# Reset post success flag (used to notify user)
post_success = st.session_state.post_success
if post_success:
    st.session_state.post_success = False

# Sidebar: ticket list
st.sidebar.header("📬 Tickets")

if not st.session_state.tickets_data:
    st.sidebar.markdown("🎉 No ticket left to process!", unsafe_allow_html=True)
else:
    for idx, ticket in enumerate(st.session_state.tickets_data):
        # Handle potential key errors safely
        full_thread_key = 'full_thread_summary'
        if full_thread_key not in ticket:
            full_thread_key = 'full_thread_sumary'  # Try the alternate spelling
            
        summary_clean = strip_html_tags(ticket.get(full_thread_key, "No summary available"))
        last_message_summary_clean = strip_html_tags(ticket.get('last_message_summary', "No message"))
        timestamp = time_ago(ticket.get("last_message_timestamp", "2025-01-01 00:00:00"))

        st.sidebar.markdown(f"""
        <div style='text-align: left; padding-bottom: 0.2em;'>
            {"🔒 " if ticket.get("needs_human", False) else ""}<strong>{summary_clean}</strong><br>
            <span>{last_message_summary_clean}</span><br>
            <small>{ticket.get('customer', 'Unknown')} ({ticket.get('theme', 'Unknown')}) · {timestamp}</small><br>
        </div>
        """, unsafe_allow_html=True)

        if st.sidebar.button("View ticket 🡺", key=f"ticket_{ticket['id']}"):
            st.session_state.selected_ticket = idx

st.sidebar.divider()

if st.sidebar.button("🔄 Refresh Tickets"):
    with st.spinner("Refreshing ticket data..."):
        preprocess_open_tickets.run_preprocessing()
        st.session_state.preprocessing_done = True
        if "tickets_data" in st.session_state:
            del st.session_state.tickets_data
        st.success("✅ Ticket data refreshed!")
        st.rerun()

cols = st.columns([2, 1])

# Show success message if post was successful
if post_success:
    st.success("✅ Reply posted to Ticksy successfully!")

# === LEFT: Ticket content ===
if not st.session_state.tickets_data:
    st.markdown("No ticket left to process. All done! 🎉", unsafe_allow_html=True)
else:
    # Main panel: show selected ticket
    selected_idx = st.session_state.selected_ticket
    if selected_idx is None or selected_idx >= len(st.session_state.tickets_data):
        # Reset to a valid index or None
        if len(st.session_state.tickets_data) > 0:
            st.session_state.selected_ticket = 0
            selected_idx = 0
        else:
            st.session_state.selected_ticket = None
            st.markdown("ℹ️ No ticket selected.", unsafe_allow_html=True)
    
    # Only proceed if we have a valid ticket
    if selected_idx is not None and selected_idx < len(st.session_state.tickets_data):
        with cols[0]:
            ticket = st.session_state.tickets_data[selected_idx]
            # Only show discussion if there's more than one message
            if len(ticket.get("full_thread", [])) > 1:
                with st.expander("📜 Show Full Discussion"):
                    comments = ticket["full_thread"]

                    # Remove last message (already shown separately)
                    comments = comments[1:]

                    # Remove what was originally the last (now first) before reversing
                    if comments:
                        comments = list(reversed(comments))    # reverse to get oldest first

                    for c in comments:
                        name = c.get("commenter_name", "Unknown")
                        role = "User" if c.get("user_type") == "user" else "Support"
                        timestamp = c.get("time_stamp", "")
                        comment_html = unescape(c.get("comment", ""))

                        # ⬇️ Display attachments if present
                        if "attachments" in c and c["attachments"]:
                            st.markdown("**Attached file(s):**")
                            for file in c["attachments"]:
                                st.markdown(
                                    f'<div style="border-left: 3px solid #ddd; padding-left: 10px; margin: 5px 0;">'
                                    f'📎 <a href="{file.get("file_url", "#")}" target="_blank" style="text-decoration: none; color: #0073aa;">'
                                    f'{file.get("file_name", "Attachment")}</a></div>',
                                    unsafe_allow_html=True
                                )

                        st.markdown(f"**[{role}] {name}** — *{timestamp}*", unsafe_allow_html=True)
                        st.markdown(comment_html, unsafe_allow_html=True)
                        st.markdown("---")

            # Handle potential key errors safely
            full_thread_key = 'full_thread_summary'
            if full_thread_key not in ticket:
                full_thread_key = 'full_thread_sumary'  # Try the alternate spelling
                
            single_summary_clean = strip_html_tags(ticket.get(full_thread_key, "No summary available"))
            st.subheader(f"🗨️ {single_summary_clean}")
            st.markdown(html.unescape(ticket.get("last_message", "")), unsafe_allow_html=True)

            # ⬇️ Display attachments if present
            if "full_thread" in ticket and ticket["full_thread"]:
                first_comment = ticket["full_thread"][0]
                if "attachments" in first_comment and first_comment["attachments"]:
                    st.markdown("**Attached file(s):**")
                    for file in first_comment["attachments"]:
                        st.markdown(
                            f'<div style="border-left: 3px solid #ddd; padding-left: 10px; margin: 5px 0;">'
                            f'📎 <a href="{file.get("file_url", "#")}" target="_blank" style="text-decoration: none; color: #0073aa;">'
                            f'{file.get("file_name", "Attachment")}</a></div>',
                            unsafe_allow_html=True
                        )

            st.divider()

            ticket_id = ticket["id"]
            editor_state_key = f"editor_reply_{ticket_id}"
            initial_content = ""

            # Use text area with default values
            if crew_instruction_key not in st.session_state:
                st.session_state[crew_instruction_key] = ""
            
            crew_instruction = st.text_area("📝 Paste an optional note here:", key=crew_instruction_key)
            
            if st.button("🤖 Generate / Regenerate Reply"):
                with st.spinner("Generating reply..."):
                    try:
                        result = support_crew_with_research(ticket["last_message"], instruction=crew_instruction, ticket_id=ticket_id)
                        
                        reply_html = result["reply"].output if hasattr(result["reply"], "output") else result["reply"]
                        
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

            # Set default before widget
            if reformulate_instruction_key not in st.session_state:
                st.session_state[reformulate_instruction_key] = ""
                
            reformulate_instruction = st.text_area("Optional reformulation", key=reformulate_instruction_key)
            
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
                close_ticket = st.checkbox("Close Ticket", value=st.session_state.close_ticket_checkbox, key="close_ticket_checkbox")

            with col2:
                # Callback to handle posting
                def handle_post_reply():
                    current_reply = get_tinymce_content(ticket_id)
                    if not current_reply.strip():
                        st.warning("⚠️ Editor is empty — nothing to post.")
                        return
                        
                    result = post_to_ticksy(ticket_id=ticket_id, message=current_reply, close_ticket=close_ticket)
                    if result.get("status") == "ok":
                        # Set flag to clear inputs on next rerun
                        st.session_state.clear_instruction = True
                        st.session_state.post_success = True
                            
                        # Clean up editor state
                        if editor_state_key in st.session_state:
                            del st.session_state[editor_state_key]

                        delete_tinymce_draft(ticket_id)

                        # Remove the ticket from session state
                        st.session_state.tickets_data = [t for t in st.session_state.tickets_data if t['id'] != ticket_id]
                        
                        # Update the selected ticket if needed
                        if st.session_state.tickets_data:
                            # If we have remaining tickets, select the first one
                            st.session_state.selected_ticket = 0
                        else:
                            # If no tickets left, set to None
                            st.session_state.selected_ticket = None

                        st.rerun()
                    else:
                        st.error("❌ Failed to post. Check console/logs.")

                if st.button("✅ Post Reply to Ticksy"):
                    handle_post_reply()

        # === RIGHT: Ticket metadata ===
        with cols[1]:
            st.markdown("### 🧾 Ticket Info")
            st.markdown(f"**Theme:** {ticket.get('theme', 'Unknown')}")
            st.markdown(f"**Customer:** [{ticket.get('customer', 'Unknown')}]({ticket.get('customer_url', '#')})")
            st.markdown(f"**Website:** {ticket.get('user_site', 'Not specified')}")
            st.markdown(f"**Ticket Link:** [#{ticket_id}]({ticket.get('ticket_url', '#')})")