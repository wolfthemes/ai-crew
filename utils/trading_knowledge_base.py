import os
import glob
from pathlib import Path

class TradingKnowledgeBase:
    """
    A simplified class for loading and accessing trading knowledge from markdown files.
    Works with the existing project structure and complements the DailyBiasFramework.
    """
    
    def __init__(self, md_dir="static/trading_rules/visuals", visuals_dir="static/trading_rules/visuals/visuals"):
        """
        Initialize the trading knowledge base loader.

        Args:
            md_dir (str): Directory where markdown knowledge base files are stored
            visuals_dir (str): Directory where visual assets (images) are stored
        """
        self.md_dir = md_dir
        self.visuals_dir = visuals_dir
        self.markdown_docs = {}
        self.visuals = {}

        # Load markdown documents
        self._load_markdown_docs()
        # Load visuals
        self._load_visuals()

    def _load_markdown_docs(self):
        """Load all markdown files from the base directory"""
        if not os.path.exists(self.md_dir):
            print(f"Warning: Markdown directory {self.md_dir} does not exist")
            return

        # Get all markdown files in the directory
        md_files = glob.glob(os.path.join(self.md_dir, "*.md"))

        for md_file in md_files:
            try:
                # Extract the file name without extension as the key
                file_name = os.path.basename(md_file).replace(".md", "")

                # Read the markdown content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Store the content
                self.markdown_docs[file_name] = {
                    "content": content,
                    "file_path": md_file
                }

                print(f"Loaded markdown doc: {file_name}")
            except Exception as e:
                print(f"Error loading {md_file}: {e}")

    def _load_visuals(self):
        """Load all image files from the visuals directory"""
        if not os.path.exists(self.visuals_dir):
            print(f"Warning: Visuals directory {self.visuals_dir} does not exist")
            return

        # Supported image extensions
        image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.webp"]
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(self.visuals_dir, ext)))

        for img_file in image_files:
            try:
                file_name = os.path.basename(img_file)
                self.visuals[file_name] = {
                    "file_path": img_file,
                    "relative_path": os.path.relpath(img_file, self.visuals_dir)
                }
                print(f"Loaded visual: {file_name}")
            except Exception as e:
                print(f"Error loading visual {img_file}: {e}")

    def get_document(self, name):
        """
        Get a specific markdown document by name

        Args:
            name (str): Name of the document (without .md extension)

        Returns:
            dict: Document content if found, None otherwise
        """
        return self.markdown_docs.get(name)

    def get_all_documents(self):
        """Get all markdown documents"""
        return self.markdown_docs

    def get_visual(self, name):
        """
        Get a specific visual (image) by file name

        Args:
            name (str): Name of the image file (e.g. 'pattern1.png')

        Returns:
            dict: Visual info if found, None otherwise
        """
        return self.visuals.get(name)

    def get_all_visuals(self):
        """Get all loaded visuals (images)"""
        return self.visuals

    def search_documents(self, query):
        """
        Search the markdown documents for a query

        Args:
            query (str): Search query

        Returns:
            dict: Dictionary of search results
        """
        results = {}
        query = query.lower()

        for name, doc in self.markdown_docs.items():
            if query in doc["content"].lower():
                results[name] = {
                    "name": name,
                    "content": doc["content"],
                    "file_path": doc["file_path"]
                }

        return results

def get_context_for_agent(self, agent_type):
    """
    Get relevant context for a specific agent type

    Args:
        agent_type (str): Type of agent (e.g., 'technical', 'fundamental')

    Returns:
        str: Context string
    """
    context = ""

    # Define which documents are relevant for each agent type
    relevant_docs = {
        'technical': ['technical_patterns', 'entry_rules', 'scenario_examples'],
        'fundamental': ['fundamental_context', 'glossary'],
        'daily_bias': ['Daily Report Prompt', 'checklists'],
        'weekly_profile': ['trading_overview', 'scenario_examples'],
        'sentiment': ['fundamental_context'],
        'entry_model': ['checklists', 'entry_rules']
    }

    # Default to all documents if agent type not recognized
    docs_to_include = relevant_docs.get(agent_type, self.markdown_docs.keys())

    # Build context from relevant documents
    for doc_name in docs_to_include:
        doc = self.get_document(doc_name)
        if doc:
            context += f"--- {doc_name.upper().replace('_', ' ')} ---\n\n"
            context += doc["content"]
            context += "\n\n"

    return context if context else f"No specific knowledge found for {agent_type} agent."

# Example usage
if __name__ == "__main__":
    kb = TradingKnowledgeBase()
    print(f"Loaded {len(kb.markdown_docs)} markdown documents")
    
    # Test getting a specific document
    tech_patterns = kb.get_document("technical_patterns")
    if tech_patterns:
        print(f"Technical patterns document is {len(tech_patterns['content'])} characters long")

    # Test getting a specific visual
    visual = kb.get_visual("CISD.webp")
    if visual:
        print(f"Visual CISD.webp path: {visual['file_path']}")
    
    # Test getting context for an agent
    technical_context = kb.get_context_for_agent("technical")
    print(f"Technical agent context is {len(technical_context)} characters long")