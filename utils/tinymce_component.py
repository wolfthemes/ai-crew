import os
import streamlit as st
import streamlit.components.v1 as components
import uuid

def tinymce_editor(initial_content="", ticket_id="0", height=500):
    """
    Render a TinyMCE editor and return its content.
    
    Parameters:
    - initial_content: The starting content for the editor
    - height: Editor height in pixels
    
    Returns:
    - The editor content
    """
    # Generate a unique ID
    editor_id = f"editor_{uuid.uuid4().hex[:8]}"
    TINYMCE_API_KEY = os.getenv("TINYMCE_API_KEY")
    #editor_provider_url = f"https://cdn.tiny.cloud/1/{TINYMCE_API_KEY}/tinymce/7/tinymce.min.js"
    #editor_provider_url = "https://hugerte.org/node_modules/hugerte/hugerte.min.js?v=1.0.9" # <- replace with local URL
    editor_provider_url = "https://cdn.jsdelivr.net/npm/hugerte@1.0.9/hugerte.min.js"

    component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="{editor_provider_url}" referrerpolicy="origin"></script>
        <style>
            body {{ margin: 0; }}
        </style>
    </head>
    <body>
        <textarea id="{editor_id}">{initial_content}</textarea>
        <script>
            const editorId = "{editor_id}";
            const saveToFile = () => {{
                const content = hugerte.get(editorId).getContent();
                console.log(content)
                fetch("http://localhost:5050/save_editor_content", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json"
                }},
                    body: JSON.stringify({{
                        html: content,
                        ticket_id: {ticket_id}
                    }})
                }})
                .then(response => response.json())
                .then(data => console.log("✅ Sent to Python:", data))
                .catch(error => console.error("❌ Error posting:", error));
            }};

            hugerte.init({{
                selector: "#" + editorId,
                height: {height},
                menubar: false,
                plugins: "link lists code codesample",
                link_default_target: '_blank',
                codesample_languages: [
                    {{ text: 'CSS', value: 'css' }},
                    {{ text: 'JavaScript', value: 'javascript' }},
                    {{ text: 'PHP', value: 'php' }},
                    {{ text: 'HTML/XML', value: 'markup' }},
                    {{ text: 'Python', value: 'python' }}
                ],
                toolbar: "undo redo | bold italic | bullist numlist | link | code | codesample",
                setup: function (editor) {{
                    editor.on("Change KeyUp", saveToFile);
                    
                    // Add a blur event to ensure we capture the final content
                    editor.on("blur", saveToFile);
                }},
                init_instance_callback: function (editor) {{
                    // Send initial content after initialization
                    saveToFile();
                }}
            }});
        </script>
    </body>
    </html>
    """

    # Return the content of the editor
    return components.html(component_html, height=height)

def get_tinymce_content(ticket_id: str) -> str:
    path = f"data/dynamic/editor/draft_{ticket_id}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def delete_tinymce_draft(ticket_id: str) -> None:
    path = f"data/dynamic/editor/draft_{ticket_id}"
    try:
        os.remove(path)
        print(f"Deleted: {path}")
    except FileNotFoundError:
        print(f"No draft found for ticket {ticket_id} (nothing to delete).")