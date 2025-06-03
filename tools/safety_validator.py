import os
import subprocess

from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = os.getenv("LOCAL_REPOS_DIR")

class SafetyValidator:
    """Base class for validating operations according to safety rules"""
    
    @staticmethod
    def is_ai_branch(branch_name):
        """Check if branch name contains 'ai-' or '-ai'"""
        return branch_name and (branch_name.startswith('ai-') or '-ai' in branch_name)
    
    @staticmethod
    def get_current_branch(repo_name):
        """Get the current branch name for a repository"""
        repo_path = os.path.join(REPO_ROOT, repo_name)
        
        if not os.path.exists(repo_path):
            return None
        
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return None
    
    @classmethod
    def validate_branch_for_write_operation(cls, repo_name, branch_name=None):
        """Validate branch name for write operations
        
        Args:
            repo_name: The repository name
            branch_name: Branch name (if None, gets current branch)
            
        Returns:
            tuple: (is_valid, message)
        """
        # Get current branch if none provided
        if branch_name is None:
            branch_name = cls.get_current_branch(repo_name)
            
        if not branch_name:
            return False, f"❌ Could not determine branch for repo '{repo_name}'"
            
        # Check if branch name follows AI naming convention
        if not cls.is_ai_branch(branch_name):
            return False, f"⚠️ Safety restriction: Can only perform write operations on branches with 'ai-' or '-ai' in the name. '{branch_name}' is not allowed."
        
        return True, f"✅ Branch '{branch_name}' is valid for write operations"
    
    @classmethod
    def create_ai_branch_if_needed(cls, repo_name, force=False):
        """Create an AI branch if we're not already on one
        
        Args:
            repo_name: The repository name
            force: If True, creates a new branch even if current is AI
            
        Returns:
            tuple: (success, message, branch_name)
        """
        current_branch = cls.get_current_branch(repo_name)
        
        # Already on AI branch and not forcing new branch
        if not force and cls.is_ai_branch(current_branch):
            return True, f"Already on AI branch: {current_branch}", current_branch
            
        # Create a new AI branch
        repo_path = os.path.join(REPO_ROOT, repo_name)
        new_branch = f"ai-dev-{os.urandom(4).hex()}"
        
        try:
            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", new_branch],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            return True, f"Created and switched to new AI branch: {new_branch}", new_branch
        except subprocess.CalledProcessError as e:
            return False, f"❌ Failed to create AI branch: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}", None
