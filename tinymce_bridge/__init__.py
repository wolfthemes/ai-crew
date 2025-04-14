import streamlit.components.v1 as components

_component = components.declare_component(
    "tinymce_reply_bridge",
    path="frontend/public"
)

def get_editor_reply(default=""):
    return _component(default=default)
