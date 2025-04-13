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
            #streamlit-bridge {{ display: none; }}
        </style>
    </head>
    <body>
        <textarea id="{editor_id}">{initial_content}</textarea>
        <textarea id="streamlit-bridge"></textarea>

        <script>
            const editorId = "{editor_id}";
            const streamlitBridge = document.getElementById("streamlit-bridge");

            const sendToStreamlit = () => {{
                const content = tinymce.get(editorId).getContent();
                streamlitBridge.value = content;
                streamlitBridge.dispatchEvent(new Event("input", {{ bubbles: true }}));
                console.log("✅ Synced to Streamlit:", content);
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
                    setTimeout(sendToStreamlit, 200);
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(component_html, height=height + 60)
