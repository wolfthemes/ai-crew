from typing import Dict, List, Any, Optional
import jinja2


class ResponseTemplates:
    """
    Provides response templates for different query types.
    Helps ensure consistent formatting and style in dev agent responses.
    """
    
    # Template for code existence queries
    CODE_EXISTENCE_TEMPLATE = """
{%- if exists %}
✅ **Found**: The {{ element_type }} `{{ element_name }}` {{ exists_statement }} in {{ location }}.

{% if occurrences_count > 1 %}
It appears {{ occurrences_count }} times in the codebase:

{% for occurrence in occurrences %}
- **{{ occurrence.file }}:{{ occurrence.line }}**: {{ occurrence.snippet }}
{% endfor %}
{% else %}
**Location**: {{ occurrences[0].file }}:{{ occurrences[0].line }}

**Context**:
```{{ language }}
{{ occurrences[0].context }}
```
{% endif %}

{% if additional_info %}
{{ additional_info }}
{% endif %}
{%- else %}
❌ **Not Found**: The {{ element_type }} `{{ element_name }}` was not found in {{ location }}.

{% if suggestions %}
**Suggestions**:
{% for suggestion in suggestions %}
- {{ suggestion }}
{% endfor %}
{% endif %}
{%- endif %}
"""

    # Template for code content queries
    CODE_CONTENT_TEMPLATE = """
{% if content %}
{% if title %}**{{ title }}**{% endif %}

```{{ language }}
{{ content }}
```

{% if explanation %}
**Explanation**:
{{ explanation }}
{% endif %}
{% else %}
❌ **Not Found**: Could not retrieve the requested code content.

{% if error %}
**Error**: {{ error }}
{% endif %}

{% if suggestions %}
**Suggestions**:
{% for suggestion in suggestions %}
- {{ suggestion }}
{% endfor %}
{% endif %}
{%- endif %}
"""

    # Template for code structure queries
    CODE_STRUCTURE_TEMPLATE = """
**Code Structure Analysis**: {{ file_path }}

{% if elements %}
{% if element_type == 'functions' %}
### Functions:
{% for func in elements %}
- `{{ func.name }}` ({{ func.line }}){% if func.params %} - Parameters: {{ func.params }}{% endif %}
{% endfor %}
{% elif element_type == 'classes' %}
### Classes:
{% for cls in elements %}
- `{{ cls.name }}` ({{ cls.line }})
  {% if cls.methods %}
  **Methods**: {{ cls.methods|join(', ') }}
  {% endif %}
  {% if cls.properties %}
  **Properties**: {{ cls.properties|join(', ') }}
  {% endif %}
{% endfor %}
{% elif element_type == 'imports' %}
### Imports:
{% for imp in elements %}
- `{{ imp.module }}{% if imp.name %}` imports `{{ imp.name }}{% endif %}` ({{ imp.line }})
{% endfor %}
{% else %}
### Elements:
{% for elem in elements %}
- `{{ elem.name }}` ({{ elem.line }})
{% endfor %}
{% endif %}

{% if relationships %}
### Relationships:
{% for rel in relationships %}
- {{ rel }}
{% endfor %}
{% endif %}

{% else %}
No {{ element_type }} were found in {{ file_path }}.
{% endif %}
"""

    # Template for code modification results
    CODE_MODIFICATION_TEMPLATE = """
{% if success %}
✅ **Success**: The code modification was completed successfully.

**Changes**:
{% for change in changes %}
- {{ change }}
{% endfor %}

{% if before_after %}
**Before**:
```{{ language }}
{{ before_after.before }}
```

**After**:
```{{ language }}
{{ before_after.after }}
```
{% endif %}

{% else %}
❌ **Error**: Could not modify the code.

{% if error %}
**Issue**: {{ error }}
{% endif %}

{% if suggestions %}
**Suggestions**:
{% for suggestion in suggestions %}
- {{ suggestion }}
{% endfor %}
{% endif %}
{%- endif %}
"""

    # Template for file operation results
    FILE_OPERATION_TEMPLATE = """
{% if success %}
✅ **Success**: {{ operation_type }} operation completed successfully.

{% if details %}
**Details**:
{% for detail in details %}
- {{ detail }}
{% endfor %}
{% endif %}

{% else %}
❌ **Error**: {{ operation_type }} operation failed.

{% if error %}
**Issue**: {{ error }}
{% endif %}

{% if suggestions %}
**Suggestions**:
{% for suggestion in suggestions %}
- {{ suggestion }}
{% endfor %}
{% endif %}
{%- endif %}
"""

    # Template for git operation results
    GIT_OPERATION_TEMPLATE = """
{% if success %}
✅ **Success**: Git {{ operation_type }} completed.

{% if details %}
**Details**:
{% for detail in details %}
- {{ detail }}
{% endfor %}
{% endif %}

{% else %}
❌ **Error**: Git {{ operation_type }} failed.

{% if error %}
**Issue**: {{ error }}
{% endif %}

{% if suggestions %}
**Suggestions**:
{% for suggestion in suggestions %}
- {{ suggestion }}
{% endfor %}
{% endif %}
{%- endif %}
"""

    # Template for WordPress specific responses
    WORDPRESS_TEMPLATE = """
{% if title %}**{{ title }}**{% endif %}

{% if content %}
{{ content }}
{% endif %}

{% if code_example %}
**Example**:
```php
{{ code_example }}
```
{% endif %}

{% if reference %}
**WordPress Reference**:
{% for ref in reference %}
- {{ ref }}
{% endfor %}
{% endif %}
"""

    # Template for general explanations
    GENERAL_EXPLANATION_TEMPLATE = """
{% if title %}**{{ title }}**{% endif %}

{% if explanation %}
{{ explanation }}
{% endif %}

{% if examples %}
**Examples**:
{% for example in examples %}
{% if example.code %}
```{{ example.language }}
{{ example.code }}
```
{% else %}
- {{ example }}
{% endif %}
{% endfor %}
{% endif %}

{% if additional_resources %}
**Additional Resources**:
{% for resource in additional_resources %}
- {{ resource }}
{% endfor %}
{% endif %}
"""

    @classmethod
    def render_template(cls, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of the template to render
            context: Dictionary with variables for the template
            
        Returns:
            Rendered template as a string
        """
        template_map = {
            "code_existence": cls.CODE_EXISTENCE_TEMPLATE,
            "code_content": cls.CODE_CONTENT_TEMPLATE,
            "code_structure": cls.CODE_STRUCTURE_TEMPLATE,
            "code_modification": cls.CODE_MODIFICATION_TEMPLATE,
            "file_operation": cls.FILE_OPERATION_TEMPLATE,
            "git_operation": cls.GIT_OPERATION_TEMPLATE,
            "wordpress": cls.WORDPRESS_TEMPLATE,
            "general_explanation": cls.GENERAL_EXPLANATION_TEMPLATE
        }
        
        template_str = template_map.get(template_name)
        if not template_str:
            return f"Error: Template '{template_name}' not found."
            
        template = jinja2.Template(template_str)
        return template.render(**context)
    
    @classmethod
    def format_code_existence_response(cls, search_results: Dict[str, Any]) -> str:
        """
        Format a response for code existence queries.
        
        Args:
            search_results: Results from the code occurrence counter tool
            
        Returns:
            Formatted response string
        """
        context = {
            "exists": search_results.get("exists", False),
            "element_type": search_results.get("element_type", "element"),
            "element_name": search_results.get("element_name", ""),
            "exists_statement": "exists" if search_results.get("exists", False) else "does not exist",
            "location": search_results.get("location", "the codebase"),
            "occurrences_count": len(search_results.get("occurrences", [])),
            "occurrences": search_results.get("occurrences", []),
            "language": search_results.get("language", "php"),
            "additional_info": search_results.get("additional_info", ""),
            "suggestions": search_results.get("suggestions", [])
        }
        
        return cls.render_template("code_existence", context)
    
    @classmethod
    def format_code_content_response(cls, content_results: Dict[str, Any]) -> str:
        """
        Format a response for code content queries.
        
        Args:
            content_results: Results from the code snippet or file content tool
            
        Returns:
            Formatted response string
        """
        context = {
            "content": content_results.get("content", ""),
            "title": content_results.get("title", ""),
            "language": content_results.get("language", "php"),
            "explanation": content_results.get("explanation", ""),
            "error": content_results.get("error", ""),
            "suggestions": content_results.get("suggestions", [])
        }
        
        return cls.render_template("code_content", context)
    
    @classmethod
    def format_code_structure_response(cls, structure_results: Dict[str, Any]) -> str:
        """
        Format a response for code structure queries.
        
        Args:
            structure_results: Results from the AST parser tool
            
        Returns:
            Formatted response string
        """
        context = {
            "file_path": structure_results.get("file_path", ""),
            "elements": structure_results.get("elements", []),
            "element_type": structure_results.get("element_type", "elements"),
            "relationships": structure_results.get("relationships", [])
        }
        
        return cls.render_template("code_structure", context)
    
    @classmethod
    def generate_response(cls, query_type: str, tool_results: Dict[str, Any], 
                          additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a formatted response based on query type and tool results.
        
        Args:
            query_type: Type of query (code_existence, code_content, etc.)
            tool_results: Results from the tools
            additional_context: Additional context to include in the response
            
        Returns:
            Formatted response string
        """
        if not additional_context:
            additional_context = {}
            
        # Combine tool results with additional context
        context = {**tool_results, **additional_context}
        
        # Format response based on query type
        if query_type == "code_existence":
            return cls.format_code_existence_response(context)
        elif query_type == "code_content":
            return cls.format_code_content_response(context)
        elif query_type == "code_structure":
            return cls.format_code_structure_response(context)
        elif query_type == "code_modification":
            return cls.render_template("code_modification", context)
        elif query_type == "file_operation":
            return cls.render_template("file_operation", context)
        elif query_type == "git_operation":
            return cls.render_template("git_operation", context)
        elif query_type == "wordpress_specific":
            return cls.render_template("wordpress", context)
        else:
            return cls.render_template("general_explanation", context)