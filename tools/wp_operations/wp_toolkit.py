import difflib
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import re

REPO_ROOT = os.path.abspath("repos")

class WPAddEnqueueInput(BaseModel):
    repo_name: str = Field(..., description="Repository name")
    file_path: str = Field(..., description="PHP file to modify (usually functions.php)")
    script_handle: str = Field(..., description="Script handle (unique identifier)")
    script_path: str = Field(..., description="Path to the JS file to enqueue")
    dependencies: str = Field(default="array()", description="JavaScript dependencies")
    in_footer: bool = Field(default=True, description="Whether to enqueue in footer")
    existing_function: str = Field(default=None, description="Existing function to add the enqueue code to")

class WordPressToolkit(BaseTool):
    name: str = "wordpress_toolkit"
    description: str = "Performs WordPress-specific operations like enqueuing scripts"
    args_schema: Type[BaseModel] = WPAddEnqueueInput

    def _run(self, repo_name: str, file_path: str, script_handle: str, script_path: str, 
             dependencies: str = "array()", in_footer: bool = True, existing_function: str = None) -> str:
        try:
            full_path = os.path.join(REPO_ROOT, repo_name, file_path)
            
            if not os.path.isfile(full_path):
                return f"❌ File not found: {full_path}"
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Create the enqueue code
            footer_val = "true" if in_footer else "false"
            enqueue_code = f"wp_enqueue_script('{script_handle}', get_template_directory_uri() . '/{script_path}', {dependencies}, '1.0.0', {footer_val});"
            
            # Store original content and create modified version
            original_content = content
            modified_content = content  # Will be updated

            if existing_function:
                # Try to insert into an existing function
                function_pattern = re.compile(r'function\s+' + re.escape(existing_function) + r'\s*\([^)]*\)\s*{', re.DOTALL)
                match = function_pattern.search(content)
                
                if match:
                    # Find the first suitable position inside the function to add our code
                    function_start = match.end()
                    # Look for the next line break after the function opening brace
                    insert_pos = content.find('\n', function_start)
                    if insert_pos > 0:
                        modified_content = content[:insert_pos] + f"\n\t{enqueue_code}" + content[insert_pos:]
                    else:
                        return f"❌ Unable to find suitable insertion point in function '{existing_function}'"
                else:
                    return f"❌ Function '{existing_function}' not found in {file_path}"
            else:
                # Create a new function
                enqueue_function = f"""
function enqueue_{script_handle}_script() {{
    {enqueue_code}
}}
add_action('wp_enqueue_scripts', 'enqueue_{script_handle}_script');
"""
                
                # Find the best place to insert - before closing PHP tag or at the end
                if '?>' in content:
                    modified_content = content.replace('?>', enqueue_function + '\n?>')
                else:
                    modified_content = content + '\n' + enqueue_function
            
            # Generate diff for preview
            diff_lines = list(difflib.unified_diff(
                original_content.splitlines(),
                modified_content.splitlines(),
                fromfile=f'a/{file_path}',
                tofile=f'b/{file_path}',
                n=3  # Context lines
            ))
            
            diff_text = '\n'.join(diff_lines)
            
            # Return a preview that requires explicit confirmation
            return f"""
## 📝 WordPress Script Enqueue Preview for {repo_name}/{file_path}

### Changes to be made:
Adding script: {script_handle} from path: {script_path}
{f"Target function: {existing_function}" if existing_function else "Creating new enqueue function"}

### Preview:
{diff_text}
"""

        except Exception as e:
            return f"❌ Error generating WordPress enqueue preview: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_name', 'file_path', 'script_handle', 'script_path'."