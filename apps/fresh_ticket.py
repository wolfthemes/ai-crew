from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import markdown2
from crews.support_crew import support_crew_with_research

st.set_page_config(page_title="Fresh Ticket", layout="centered")
st.title("WolfThemes — Fresh Ticket Reply")
st.markdown("Paste any customer message (email, forum post, etc.) and generate a support reply.")

ticket_input = st.text_area("Customer message:", height=220, placeholder="Paste the customer text here...")
crew_instruction = st.text_area("Optional note / instruction:", height=80, placeholder="e.g. 'Be brief' or 'Customer is angry'")

if st.button("Generate Reply") and ticket_input.strip():
    with st.spinner("Generating reply..."):
        try:
            result = support_crew_with_research(ticket_input.strip(), instruction=crew_instruction)

            raw = result.get("reply", "")
            if hasattr(raw, "raw"):
                reply_text = raw.raw
            elif hasattr(raw, "output"):
                reply_text = raw.output
            elif isinstance(raw, str):
                reply_text = raw
            else:
                reply_text = str(raw)

            reply_html = markdown2.markdown(reply_text)
            st.session_state["fresh_reply_html"] = reply_html
            st.session_state["fresh_reply_text"] = reply_text
        except Exception as e:
            st.error(f"Error: {e}")

if "fresh_reply_html" in st.session_state:
    st.divider()
    st.subheader("Suggested Reply")
    st.markdown(st.session_state["fresh_reply_html"], unsafe_allow_html=True)
    st.divider()
    st.text_area("Plain text (copy from here):", value=st.session_state["fresh_reply_text"], height=300)
