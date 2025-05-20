import os
import json
try:
    import PyPDF2 # type: ignore
except ImportError:
    PyPDF2 = None
    print("PyPDF2 is not installed. PDF parsing will not work.")
from typing import Dict, List, Optional, Union, Any
import re

from dotenv import load_dotenv
load_dotenv()

OBSIDIAN_DIR = os.getenv("OBSIDIAN_DIR")

class DailyBiasFramework:
    """
    Utility class for reading and managing Daily Bias framework PDF documents.
    
    This class helps load, parse, and extract concepts from the Weekly Profile, 
    Daily Bias including the Next Day model, Intraday Bias and London Reversal PDF documents, providing easy access
    to framework concepts for the market analysis agents.
    """
    
    def __init__(self, framework_dir=None):
        """
        Initialize the framework reader.
        
        Args:
            framework_dir: Directory containing framework PDF files
        """
        #self.framework_dir = framework_dir
        self.framework_dir = framework_dir or f"{OBSIDIAN_DIR}/Resources/Trading/PDF"
        self.cache_dir = os.path.join("data", "cache", "framework")
        self.frameworks = {}
        
        # Create directories if they don't exist
        os.makedirs(self.framework_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Framework file paths
        self.files = {
            "weekly_profile": os.path.join(framework_dir, "Weekly-Profile.pdf"),
            "daily_bias": os.path.join(framework_dir, "Daily-Bias.pdf"),
            "next_day_model": os.path.join(framework_dir, "Next-Day-Model.pdf"),
            "IRL_ERL": os.path.join(framework_dir, "IRL-ERL.pdf"),
            "intraday_bias": os.path.join(framework_dir, "Intraday-Bias.pdf"),
            "london_reversal": os.path.join(framework_dir, "London-Reversal.pdf"),
            "cisd": os.path.join(framework_dir, "Change-In-State-of-Delivery.pdf"),
            "pd_array": os.path.join(framework_dir, "PD-Array.pdf"),
            "Po3": os.path.join(framework_dir, "Power-of-3-Accumulation-Manipulation-Distribution.pdf")
        }
        
        # Cache file paths
        self.cache_files = {
            "weekly_profile": os.path.join(self.cache_dir, "weekly_profile.json"),
            "daily_bias": os.path.join(self.cache_dir, "daily_bias.json"),
            "next_day_model": os.path.join(self.cache_dir, "next_day_model.json"),
            "IRL_ERL": os.path.join(self.cache_dir, "IRL_ERL.json"),
            "intraday_bias": os.path.join(self.cache_dir, "intraday_bias.json"),
            "london_reversal": os.path.join(self.cache_dir, "london_reversal.json"),
            "cisd": os.path.join(self.cache_dir, "cisd.json"),
            "pd_array": os.path.join(self.cache_dir, "pd_array.json"),
            "Po3": os.path.join(self.cache_dir, "Po3.json")
        }
        
        # Load frameworks from cache or PDF files
        self._load_frameworks()
    
    def _load_frameworks(self) -> None:
        """
        Load all framework documents from cache if available, otherwise parse PDFs.
        """
        for name, cache_file in self.cache_files.items():
            pdf_file = self.files[name]
            
            # Check if cache exists and is newer than PDF
            if os.path.exists(cache_file) and os.path.exists(pdf_file):
                cache_mtime = os.path.getmtime(cache_file)
                pdf_mtime = os.path.getmtime(pdf_file)
                
                if cache_mtime > pdf_mtime:
                    # Cache is newer than PDF, load from cache
                    try:
                        with open(cache_file, 'r') as f:
                            self.frameworks[name] = json.load(f)
                        print(f"Loaded {name} framework from cache")
                        continue
                    except Exception as e:
                        print(f"Error loading {name} cache: {e}")
            
            # Cache doesn't exist or is outdated, parse PDF
            if os.path.exists(pdf_file):
                try:
                    content = self._extract_pdf_text(pdf_file)
                    self.frameworks[name] = self._parse_framework(content, name)
                    
                    # Save to cache
                    with open(cache_file, 'w') as f:
                        json.dump(self.frameworks[name], f, indent=2)
                    
                    print(f"Parsed and cached {name} framework")
                except Exception as e:
                    print(f"Error parsing {name} PDF: {e}")
            else:
                print(f"Warning: {name} PDF file not found at {pdf_file}")
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def _parse_framework(self, content: str, framework_type: str) -> Dict[str, Any]:
        """
        Parse the framework content based on its type.
        
        Args:
            content: The text content of the framework
            framework_type: The type of framework being parsed
            
        Returns:
            Structured dictionary of framework concepts
        """
        if framework_type == "daily_bias":
            return self._parse_daily_bias(content)
        elif framework_type == "weekly_profile":
            return self._parse_weekly_profile(content)
        elif framework_type == "next_day_model":
            return self._parse_next_day_model(content)
        else:
            return {"content": content}
    
    def _parse_daily_bias(self, content: str) -> Dict[str, Any]:
        """
        Parse the Daily Bias framework document.
        
        Args:
            content: Text content of the Daily Bias PDF
            
        Returns:
            Structured dictionary of Daily Bias concepts
        """
        # Basic structure for parsed content
        parsed = {
            "key_concepts": [],
            "price_levels": [],
            "action_patterns": [],
            "raw_content": content
        }
        
        # Extract key concepts using regex
        concept_pattern = r"(Concept|Pattern|Rule)\s*\d+:\s*([^\n]+)"
        for match in re.finditer(concept_pattern, content, re.IGNORECASE):
            parsed["key_concepts"].append(match.group(2).strip())
        
        # Extract price level references
        level_pattern = r"(support|resistance|level|high|low)[^\n,.]*\d+\.\d+"
        for match in re.finditer(level_pattern, content, re.IGNORECASE):
            parsed["price_levels"].append(match.group(0).strip())
        
        # Extract action patterns
        action_pattern = r"(buy|sell|long|short|enter|exit)[^\n.]*\."
        for match in re.finditer(action_pattern, content, re.IGNORECASE):
            parsed["action_patterns"].append(match.group(0).strip())
        
        return parsed
    
    def _parse_weekly_profile(self, content: str) -> Dict[str, Any]:
        """
        Parse the Weekly Profile framework document.
        
        Args:
            content: Text content of the Weekly Profile PDF
            
        Returns:
            Structured dictionary of Weekly Profile concepts
        """
        parsed = {
            "profile_types": [],
            "characteristics": {},
            "raw_content": content
        }
        
        # Extract profile types
        profile_pattern = r"(Profile|Type)\s*\d+:\s*([^\n]+)"
        for match in re.finditer(profile_pattern, content, re.IGNORECASE):
            profile = match.group(2).strip()
            parsed["profile_types"].append(profile)
            parsed["characteristics"][profile] = []
        
        # Extract characteristics for each profile type
        for profile in parsed["profile_types"]:
            char_pattern = rf"{re.escape(profile)}[^\n]*\n(.*?)(?=\n\n|\Z)"
            matches = re.finditer(char_pattern, content, re.DOTALL)
            for match in matches:
                characteristics = match.group(1).strip().split("\n")
                parsed["characteristics"][profile].extend([c.strip() for c in characteristics if c.strip()])
        
        return parsed
    
    def _parse_next_day_model(self, content: str) -> Dict[str, Any]:
        """
        Parse the Next Day Model framework document.
        
        Args:
            content: Text content of the Next Day Model PDF
            
        Returns:
            Structured dictionary of Next Day Model concepts
        """
        parsed = {
            "rules": [],
            "scenarios": {},
            "raw_content": content
        }
        
        # Extract rules
        rule_pattern = r"(Rule|Principle)\s*\d+:\s*([^\n]+)"
        for match in re.finditer(rule_pattern, content, re.IGNORECASE):
            parsed["rules"].append(match.group(2).strip())
        
        # Extract scenarios
        scenario_pattern = r"(Scenario|Case)\s*\d+:\s*([^\n]+)"
        for match in re.finditer(scenario_pattern, content, re.IGNORECASE):
            scenario = match.group(2).strip()
            parsed["scenarios"][scenario] = []
            
            # Try to find the guidance for this scenario
            guidance_pattern = rf"{re.escape(scenario)}[^\n]*\n(.*?)(?=\n\n|\Z)"
            guidance_matches = re.finditer(guidance_pattern, content, re.DOTALL)
            for g_match in guidance_matches:
                guidance = g_match.group(1).strip().split("\n")
                parsed["scenarios"][scenario].extend([g.strip() for g in guidance if g.strip()])
        
        return parsed
    
    def get_framework(self, name: str) -> Dict[str, Any]:
        """
        Get a specific framework by name.
        
        Args:
            name: Name of the framework ('daily_bias', 'weekly_profile', or 'next_day_model')
            
        Returns:
            Dictionary containing the framework data
        """
        if name in self.frameworks:
            return self.frameworks[name]
        else:
            print(f"Framework '{name}' not found")
            return {}
    
    def get_framework_summary(self, name: str) -> str:
        """
        Get a summarized version of a framework for use in analysis.
        
        Args:
            name: Name of the framework ('daily_bias', 'weekly_profile', or 'next_day_model')
            
        Returns:
            String containing a summary of key framework concepts
        """
        if name not in self.frameworks:
            return f"Framework '{name}' not found"
        
        framework = self.frameworks[name]
        
        if name == "daily_bias":
            concepts = "\n".join([f"- {c}" for c in framework.get("key_concepts", [])])
            return f"DAILY BIAS FRAMEWORK SUMMARY:\n\nKey Concepts:\n{concepts}\n\n"
            
        elif name == "weekly_profile":
            profiles = "\n".join([f"- {p}" for p in framework.get("profile_types", [])])
            return f"WEEKLY PROFILE FRAMEWORK SUMMARY:\n\nProfile Types:\n{profiles}\n\n"
            
        elif name == "next_day_model":
            rules = "\n".join([f"- {r}" for r in framework.get("rules", [])])
            return f"NEXT DAY MODEL FRAMEWORK SUMMARY:\n\nKey Rules:\n{rules}\n\n"
        
        return "Unknown framework type"
    
    def get_all_frameworks_context(self) -> str:
        """
        Get a combined context string containing summaries of all frameworks.
        
        Returns:
            String containing summaries of all frameworks
        """
        context = "TRADING FRAMEWORK SUMMARIES:\n\n"
        
        for name in ["daily_bias", "weekly_profile", "next_day_model"]:
            if name in self.frameworks:
                context += self.get_framework_summary(name) + "\n"
        
        return context


# Example usage
if __name__ == "__main__":
    framework_reader = DailyBiasFramework()
    
    # Get a specific framework
    daily_bias = framework_reader.get_framework("daily_bias")
    if daily_bias:
        print(f"Daily Bias Framework has {len(daily_bias.get('key_concepts', []))} key concepts")
    
    # Get a summary for context
    context = framework_reader.get_all_frameworks_context()
    print("\nFramework Context Preview:")
    print(context[:500] + "..." if len(context) > 500 else context)