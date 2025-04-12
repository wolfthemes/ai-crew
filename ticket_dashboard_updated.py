
import streamlit as st
import os
import json
import html
import streamlit.components.v1 as components
from dotenv import load_dotenv
from crews.support_crew import support_crew_with_research
from utils.helpers import time_ago, strip_html_tags

load_dotenv()

TINYMCE_API_KEY = os.getenv("TINYMCE_API_KEY")

# Load preprocessed tickets
with open("data/dynamic/preprocessed_tickets.json", encoding="utf-8") as f:
    tickets_data = json.load(f)["preprocessed_tickets"]

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
        with st.spinner("Generating reply..."):
            try:
                result = support_crew_with_research(ticket["last_message"], instruction=crew_instruction)

                # ✅ Debug output to console
                print("🧠 Crew Reply →", result["reply"])

                # ✅ Store to session
                st.session_state.generated_reply = result["reply"]
                st.session_state.reply = result["reply"]  # Ensure it's in the editor too
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error running agent: {str(e)}")


    st.subheader("✍️ Edit and Post Reply (HTML)")

    # Prioritize the most recent crew outputs
    if "reformulated_reply" in st.session_state:
        st.session_state.reply = st.session_state.reformulated_reply
        del st.session_state.reformulated_reply
    elif "generated_reply" in st.session_state:
        st.session_state.reply = st.session_state.generated_reply
        del st.session_state.generated_reply

    # Optional: session-state default
    if "reply" not in st.session_state:
        st.session_state.reply = "<p><strong>Welcome!</strong> This is a test HTML message.</p>"

    # Save edited HTML using a hidden input
    components.html(f"""
    <script src="https://cdn.tiny.cloud/1/{TINYMCE_API_KEY}/tinymce/7/tinymce.min.js" referrerpolicy="origin"></script>
    <textarea id="editor">{st.session_state.reply}</textarea>
    <script>
        tinymce.init({{
        selector: '#editor',
        height: 300,
        menubar: false,
        plugins: 'link lists code',
        toolbar: 'undo redo | bold italic | bullist numlist | link | code',
        setup: function (editor) {{
            editor.on('Change KeyUp', function (e) {{
            window.parent.postMessage({{type: 'html_update', content: editor.getContent()}}, '*');
            }});
        }}
        }});
    </script>
    """, height=350)

    # Display preview
    #st.markdown("### 🔍 Live Preview")
    #st.markdown(st.session_state.reply, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    from utils.ticket_utils import reformulate_reply

    st.markdown("### ✏️ Reformulate Reply")
    reformulate_instruction = st.text_input("Optional reformulation")
    
    if st.button("♻️ Reformulate"):
        try:
            reply_text = st.session_state.reply
            if not isinstance(reply_text, str):
                reply_text = str(reply_text)
            reformulated = reformulate_reply(
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
