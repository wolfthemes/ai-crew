# tinymce_component.py
import os
import streamlit as st
import streamlit.components.v1 as components
import json
import uuid

def tinymce_editor(initial_content="", height=500):
    """
    Creates a TinyMCE editor as a Streamlit component.
    
    Args:
        initial_content: Initial HTML content for the editor
        height: Height of the editor in pixels
        
    Returns:
        The HTML content from the editor
    """
    # Generate a unique ID for this instance of the editor
    editor_id = f"editor_{uuid.uuid4().hex[:8]}"
    
    # Get API key from environment
    TINYMCE_API_KEY = os.getenv("TINYMCE_API_KEY")
    
    # Define the component HTML
    component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.tiny.cloud/1/{TINYMCE_API_KEY}/tinymce/7/tinymce.min.js" referrerpolicy="origin"></script>
        <style>
            #content-holder {{ display: none; }}
        </style>
    </head>
    # Replace the whole <body> section with this:
    <body>
        <textarea id="{editor_id}">{initial_content}</textarea>
        <script>
            const sendToStreamlit = () => {{
                const content = tinymce.get('{editor_id}').getContent();
                console.log(content);
                const target = window.parent.document.querySelector('textarea[data-streamlit-key="reply"]');
                if (target && target.value !== content) {{
                    target.value = content;
                    target.dispatchEvent(new Event("input", {{ bubbles: true }}));
                }}
            }};

            tinymce.init({{
                selector: '#{editor_id}',
                height: {height},
                menubar: false,
                plugins: 'link lists code',
                toolbar: 'undo redo | bold italic | bullist numlist | link | code',
                setup: function (editor) {{
                    editor.on('Change KeyUp', sendToStreamlit);
                    setInterval(sendToStreamlit, 1000);
                }}
            }});
        </script>
    </body>

    </html>
    """
    
    # Render the component
    components.html(
        component_html,
        height=height + 50,  # Add a bit of extra height for margins
    )
    
    # # Check if we have a POST request with our editor content
    # if editor_id in st.experimental_get_query_params():
    #     # This will happen after the form submission
    #     content = st.experimental_get_query_params()[editor_id][0]
    #     return content
    # else:
    #     # Return the initial content if we don't have a submission yet
    #     return initial_content