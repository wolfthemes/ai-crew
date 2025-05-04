from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import ast
import os

REPO_ROOT = os.path.abspath("repos")

# Input schema
class ASTParserInput(BaseModel):
    repo_path: str = Field(..., description="The name of the repo (inside 'repos/')")
    file_path: str = Field(..., description="Relative path to the file inside the repo")
    query_type: str = Field(..., description="Type of query: 'functions', 'classes', 'imports', 'function_details', 'class_details'")
    target_name: str = Field(None, description="Name of function, class, or variable to analyze (optional)")

# ASTParserTool definition
class ASTParserTool(BaseTool):
    name: str = "ast_parser_tool"
    description: str = """
    Parse Python code into AST to understand structure and relationships.
    Use this tool to:
    - List all functions in a file
    - List all classes in a file
    - Show function details (parameters, docstring, return type)
    - Show class details (methods, attributes)
    - Find where functions/variables are used
    - Analyze imports and dependencies
    """
    args_schema: Type[BaseModel] = ASTParserInput

    def _extract_functions(self, tree: ast.Module) -> list:
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
        
    def _extract_classes(self, tree: ast.Module) -> list:
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
    
    def _extract_imports(self, tree: ast.Module) -> list:
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

    def _run(self, repo_path: str, file_path: str, query_type: str, target_name: str = None) -> str:
        full_path = os.path.join(REPO_ROOT, repo_path, file_path)

        if not os.path.exists(full_path):
            return f"❌ File not found: {full_path}"
            
        if not file_path.endswith('.py'):
            return f"❌ This tool currently only supports Python files (*.py)."
            
        try:
            with open(full_path, 'r') as f:
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
                    return "❌ Must provide target_name for function_details query."
                    
                functions = self._extract_functions(tree)
                function = next((f for f in functions if f['name'] == target_name), None)
                
                if not function:
                    return f"❌ Function '{target_name}' not found in {file_path}."
                    
                return f"Function '{target_name}' details:\n" + \
                       f"- Line: {function['lineno']}\n" + \
                       f"- Arguments: {', '.join(function['args'])}\n" + \
                       f"- Docstring: {function['docstring']}\n"
                       
            elif query_type == 'class_details':
                if not target_name:
                    return "❌ Must provide target_name for class_details query."
                    
                classes = self._extract_classes(tree)
                cls = next((c for c in classes if c['name'] == target_name), None)
                
                if not cls:
                    return f"❌ Class '{target_name}' not found in {file_path}."
                    
                return f"Class '{target_name}' details:\n" + \
                       f"- Line: {cls['lineno']}\n" + \
                       f"- Methods: {', '.join(cls['methods'])}\n" + \
                       f"- Attributes: {', '.join(cls['attributes'])}\n" + \
                       f"- Bases: {', '.join(filter(None, cls['bases']))}\n" + \
                       f"- Docstring: {cls['docstring']}\n"
                       
            else:
                return f"❌ Unknown query_type '{query_type}'."
                
        except SyntaxError as e:
            return f"❌ SyntaxError in {file_path}: {str(e)}"
        except Exception as e:
            return f"❌ Error analyzing {file_path}: {str(e)}"

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_path', 'file_path', 'query_type', and optional 'target_name'."