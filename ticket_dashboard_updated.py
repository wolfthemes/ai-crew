
import streamlit as st
import json
import time
from datetime import datetime
import html

# Load preprocessed tickets
with open("data/preprocessed_tickets.json", encoding="utf-8") as f:
    tickets_data = json.load(f)["preprocessed_tickets"]

# Helper: format "time ago"
def time_ago(timestamp_str):
    try:
        posted_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        seconds = int(time.time() - posted_time.timestamp())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except:
        return "—"

st.set_page_config(layout="wide")
st.title("🛠️ Ticket Dashboard")

# Sidebar: ticket list
st.sidebar.header("📬 Tickets")

for idx, ticket in enumerate(tickets_data):
    label = "🔒 " if ticket["needs_human"] else ""
    label += f"{html.unescape(ticket['summary'])} — {ticket['customer']} ({ticket['theme']})"
    label += f" · {ticket.get('time_stamp', '')}"
    if st.sidebar.button(label, key=f"ticket_{ticket['id']}"):
        st.session_state.selected_ticket = idx

# Main panel: show selected ticket
selected_idx = st.session_state.get("selected_ticket", 0)
ticket = tickets_data[selected_idx]

cols = st.columns([2, 1])

# === LEFT: Ticket content ===
with cols[0]:
    st.subheader("🗨️ Last Message")
    with st.expander("📜 Show Full Discussion"):
        for msg in ticket["full_thread"]:
            st.markdown(html.unescape(msg))

    st.markdown(html.unescape(ticket["last_message"]))

    st.subheader("✍️ Suggested Reply")
    ai_reply = st.text_area("AI Reply", value=ticket["ai_reply"], height=180)

    note = st.text_input("Optional internal note")
    col1, col2 = st.columns(2)
    col1.button("✅ Post Reply")
    col2.button("🔄 Regenerate")

# === RIGHT: Ticket metadata ===
with cols[1]:
    st.markdown("### 🧾 Ticket Info")
    st.markdown(f"**Customer:** [{ticket['customer']}]({ticket['customer_url']})")
    st.markdown(f"**Website:** {ticket['user_site']}")
    st.markdown(f"**Theme:** {ticket['theme']} ({ticket['builder']})")
    st.markdown(f"**Ticket Link:** [View on Ticksy]({ticket['ticket_url']})")
