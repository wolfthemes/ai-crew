import os
import streamlit.components.v1 as components

_component = components.declare_component(
    "tinymce_reply_bridge",
    path=os.path.join(os.path.dirname(__file__), "public")
)

def get_editor_reply(default=""):
    return _component(default=default)
