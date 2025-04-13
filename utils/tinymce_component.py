import os
import streamlit as st
import streamlit.components.v1 as components
import uuid

def tinymce_editor(initial_content="", height=500):
    editor_id = f"editor_{uuid.uuid4().hex[:8]}"
    TINYMCE_API_KEY = os.getenv("TINYMCE_API_KEY")

    component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.tiny.cloud/1/{TINYMCE_API_KEY}/tinymce/7/tinymce.min.js" referrerpolicy="origin"></script>
        <style>
            body {{ margin: 0; }}
        </style>
    </head>
    <body>
        <textarea id="{editor_id}">{initial_content}</textarea>
        <script>
            const editorId = "{editor_id}";
            const sendToStreamlit = () => {{
                const content = tinymce.get(editorId).getContent();
                localStorage.setItem("tinymce_reply", content);
            }};

            tinymce.init({{
                selector: "#" + editorId,
                height: {height},
                menubar: false,
                plugins: "link lists code",
                toolbar: "undo redo | bold italic | bullist numlist | link | code",
                setup: function (editor) {{
                    editor.on("Change KeyUp", sendToStreamlit);
                }},
                init_instance_callback: function () {{
                    setTimeout(() => {{
                        const content = tinymce.get(editorId).getContent();
                        localStorage.setItem("tinymce_reply", content);
                    }}, 500);
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(component_html, height=height + 60)

def sync_from_localstorage(local_key="tinymce_reply", target_key="reply", interval_ms=1000):
    # Create a hidden text area that will connect to session_state
    hidden_field_label="hidden_sync_field"
    
    components.html(f"""
    <script>
    function syncFromLocalStorage() {{
        const value = localStorage.getItem("{local_key}");
        const target = window.parent.document.querySelector("textarea[aria-label='{hidden_field_label}']");
        if (target && target.value !== value) {{
            target.value = value;

            // Simulate user typing
            const event = new Event("input", {{ bubbles: true }});
            target.dispatchEvent(event);

            const change = new Event("change", {{ bubbles: true }});
            target.dispatchEvent(change);

            // Optional: Simulate a small keypress (safe fallback)
            const keyEvent = new KeyboardEvent("keydown", {{ bubbles: true, key: "a" }});
            target.dispatchEvent(keyEvent);

            console.log("✅ Synced with simulated input:", value.slice(0, 60));
        }}
    }}
    syncFromLocalStorage();
    setInterval(syncFromLocalStorage, {interval_ms});
    </script>
    """, height=0)

    st.text_area(hidden_field_label, key=target_key, label_visibility="collapsed", height=68)

