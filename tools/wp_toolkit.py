from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import re

REPO_ROOT = os.path.abspath("repos")

class WPEnqueueInput(BaseModel):
    repo_path: str = Field(..., description="Repository name")
    file_path: str = Field(..., description="PHP file to modify (usually functions.php)")
    script_handle: str = Field(..., description="Script handle (unique identifier)")
    script_path: str = Field(..., description="Path to the JS file to enqueue")
    dependencies: str = Field(default="array()", description="JavaScript dependencies")
    in_footer: bool = Field(default=True, description="Whether to enqueue in footer")

class WordPressToolkit(BaseTool):
    name: str = "wordpress_toolkit"
    description: str = "Performs WordPress-specific operations like enqueuing scripts"
    args_schema: Type[BaseModel] = WPEnqueueInput

    def _run(self, repo_path: str, file_path: str, script_handle: str, script_path: str, 
             dependencies: str = "array()", in_footer: bool = True) -> str:
        try:
            full_path = os.path.join(REPO_ROOT, repo_path, file_path)
            
            if not os.path.isfile(full_path):
                return f"❌ File not found: {full_path}"
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create the enqueue code
            footer_val = "true" if in_footer else "false"
            enqueue_code = f"""
function enqueue_{script_handle}_script() {{
    wp_enqueue_script(
        '{script_handle}',
        get_template_directory_uri() . '/{script_path}',
        {dependencies},
        '1.0.0',
        {footer_val}
    );
}}
add_action('wp_enqueue_scripts', 'enqueue_{script_handle}_script');
"""
            
            # Find the best place to insert - before closing PHP tag or at the end
            if '?>' in content:
                modified_content = content.replace('?>', enqueue_code + '\n?>')
            else:
                modified_content = content + '\n' + enqueue_code
            
            # Write back the modified file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            return f"✅ Successfully enqueued script '{script_handle}' in {repo_path}/{file_path}"
        
        except Exception as e:
            return f"❌ Error enqueuing script: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_path', 'file_path', 'script_handle', 'script_path'."