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
                localStorage.setItem("editor_id", editorId);
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

    components.html(component_html, height=450)

def submit_button_script_inline(ticket_id: str, private: bool):
    TICKSY_API_KEY = os.getenv("TICKSY_API_KEY")
    TICKSY_DOMAIN = os.getenv("TICKSY_DOMAIN")
    private_str = "true" if private else "false"

    js = f"""
    <script>
        const createBanner = (message, type = "success") => {{
            let banner = document.createElement("div");
            banner.innerText = message;
            banner.style.position = "fixed";
            banner.style.top = "20px";
            banner.style.right = "20px";
            banner.style.padding = "12px 20px";
            banner.style.zIndex = 999999;
            banner.style.borderRadius = "8px";
            banner.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
            banner.style.fontWeight = "bold";
            banner.style.color = "white";
            banner.style.backgroundColor = type === "success" ? "#4CAF50" : "#F44336";

            window.parent.document.body.appendChild(banner);
            setTimeout(() => {{
                banner.remove();
            }}, 3000);
        }}

        const btn = window.parent.document.querySelector("#post_submit");
        if (btn) {{
            btn.onclick = () => {{
                const content = localStorage.getItem("tinymce_reply");
                const ticketId = "{ticket_id}";
                const apiKey = "{TICKSY_API_KEY}";
                const domain = "{TICKSY_DOMAIN}";

                const payload = new URLSearchParams({{
                    action: "new_ticket_comment",
                    ticket_id: ticketId,
                    comment: content,
                    private: "{private_str}"
                }});

                fetch(`https://aaaapi.ticksy.com/v1/${{domain}}/${{apiKey}}`, {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/x-www-form-urlencoded"
                    }},
                    body: payload
                }})
                .then(response => response.text())
                .then(result => {{
                    console.log("✅ Ticksy response:", result);
                    createBanner("✅ Reply successfully posted!", "success");
                }})
                .catch(error => {{
                    console.error("❌ Ticksy error:", error);
                    createBanner("❌ Failed to post reply", "error");
                }});
            }};
        }} else {{
            console.warn("❌ Could not find #post_submit");
        }}
    </script>
    """
    components.html(js, height=0)
