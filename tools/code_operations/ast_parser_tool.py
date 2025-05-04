import ast
import os
from langchain.tools import BaseTool
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ASTParserInput(BaseModel):
    """Input for the AST Parser tool."""
    file_path: str = Field(..., description="Path to the file to parse")
    query_type: str = Field(..., description="Type of query: 'functions', 'classes', 'imports', 'function_details', 'class_details', 'find_usage'")
    target_name: Optional[str] = Field(None, description="Name of function, class, or variable to analyze (for targeted queries)")


class ASTParserTool(BaseTool):
    name = "ast_parser_tool"
    description = """
    Parse Python code into AST to understand structure and relationships.
    Use this tool to:
    - List all functions in a file
    - List all classes in a file
    - Show function details (parameters, docstring, return type)
    - Show class details (methods, attributes)
    - Find where functions/variables are used
    - Analyze imports and dependencies
    """
    args_schema = ASTParserInput
    
    def _extract_functions(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract all function definitions from the AST."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node) or "",
                    'returns': getattr(node, 'returns', None)
                })
        return functions
        
    def _extract_classes(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract all class definitions from the AST."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                attributes = []
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append(target.id)
                
                classes.append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'methods': methods,
                    'attributes': attributes,
                    'bases': [base.id if isinstance(base, ast.Name) else None for base in node.bases],
                    'docstring': ast.get_docstring(node) or ""
                })
        return classes
    
    def _find_usage(self, tree: ast.Module, target_name: str) -> List[Dict[str, Any]]:
        """Find where a function, class or variable is used."""
        usages = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == target_name:
                # This might be a usage
                usages.append({
                    'lineno': node.lineno,
                    'col_offset': node.col_offset,
                    'context': self._get_context(node)
                })
        return usages
    
    def _get_context(self, node: ast.AST) -> str:
        """Get the surrounding context of a node."""
        # This would need the source code to extract context
        # Simplified version returning just location
        return f"Line {node.lineno}, Column {node.col_offset}"
    
    def _extract_imports(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract all imports from the AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append({
                        'name': name.name,
                        'alias': name.asname,
                        'lineno': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    imports.append({
                        'name': f"{module}.{name.name}",
                        'alias': name.asname,
                        'lineno': node.lineno
                    })
        return imports
        
    def _run(self, file_path: str, query_type: str, target_name: Optional[str] = None) -> str:
        """Run the AST parser tool with the given parameters."""
        # Check if file exists and has correct extension
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        
        if not file_path.endswith('.py'):
            return f"Error: This tool currently only supports Python files (*.py)."
            
        try:
            with open(file_path, 'r') as f:
                code = f.read()
                
            tree = ast.parse(code)
            
            if query_type == 'functions':
                functions = self._extract_functions(tree)
                return f"Found {len(functions)} functions in {file_path}:\n" + \
                       "\n".join([f"- {func['name']} (line {func['lineno']})" for func in functions])
                       
            elif query_type == 'classes':
                classes = self._extract_classes(tree)
                return f"Found {len(classes)} classes in {file_path}:\n" + \
                       "\n".join([f"- {cls['name']} (line {cls['lineno']})" for cls in classes])
                       
            elif query_type == 'imports':
                imports = self._extract_imports(tree)
                return f"Found {len(imports)} imports in {file_path}:\n" + \
                       "\n".join([f"- {imp['name']}{' as ' + imp['alias'] if imp['alias'] else ''}" for imp in imports])
                       
            elif query_type == 'function_details':
                if not target_name:
                    return "Error: Must provide target_name for function_details query."
                    
                functions = self._extract_functions(tree)
                function = next((f for f in functions if f['name'] == target_name), None)
                
                if not function:
                    return f"Function '{target_name}' not found in {file_path}."
                    
                return f"Function '{target_name}' details:\n" + \
                       f"- Line: {function['lineno']}\n" + \
                       f"- Arguments: {', '.join(function['args'])}\n" + \
                       f"- Docstring: {function['docstring']}\n"
                       
            elif query_type == 'class_details':
                if not target_name:
                    return "Error: Must provide target_name for class_details query."
                    
                classes = self._extract_classes(tree)
                cls = next((c for c in classes if c['name'] == target_name), None)
                
                if not cls:
                    return f"Class '{target_name}' not found in {file_path}."
                    
                return f"Class '{target_name}' details:\n" + \
                       f"- Line: {cls['lineno']}\n" + \
                       f"- Methods: {', '.join(cls['methods'])}\n" + \
                       f"- Attributes: {', '.join(cls['attributes'])}\n" + \
                       f"- Bases: {', '.join(filter(None, cls['bases']))}\n" + \
                       f"- Docstring: {cls['docstring']}\n"
                       
            elif query_type == 'find_usage':
                if not target_name:
                    return "Error: Must provide target_name for find_usage query."
                    
                usages = self._find_usage(tree, target_name)
                
                if not usages:
                    return f"'{target_name}' not used in {file_path}."
                    
                return f"Found {len(usages)} usages of '{target_name}' in {file_path}:\n" + \
                       "\n".join([f"- {usage['context']}" for usage in usages])
                       
            else:
                return f"Error: Unknown query_type '{query_type}'."
                
        except SyntaxError as e:
            return f"SyntaxError in {file_path}: {str(e)}"
        except Exception as e:
            return f"Error analyzing {file_path}: {str(e)}"