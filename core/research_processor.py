import json
import logging
from core.ticket_parser import TicketParser
from tools.kb_tools import search_kb_structured
from tools.vector_retriever import retriever

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_ticket_research(ticket_text: str, ticket_meta: dict = None, additional_instructions: str = "") -> str:
    """
    Process a support ticket to extract issues and find KB matches.
    
    Args:
        ticket_text: The content of the support ticket
        ticket_meta: Optional metadata about the ticket (theme, builder, etc.)
        additional_instructions: Optional instructions from the human operator
        
    Returns:
        JSON string with structured research results
    """
    try:
        logger.info("Starting ticket research processing")
        
        # Initialize a safe result structure
        results = []
        
        # Handle case with ticket metadata
        if ticket_meta and isinstance(ticket_meta, dict):
            logger.info("Processing with ticket metadata")
            
            # Get the last message or use ticket_text as fallback
            last_msg = ticket_text
            if "last_message" in ticket_meta and ticket_meta["last_message"]:
                last_msg = str(ticket_meta["last_message"])
            
            # Create safe context from ticket_meta
            context = {}
            # Note: Handle both spellings of summary due to typo in dashboard
            if "theme" in ticket_meta:
                context["theme"] = str(ticket_meta["theme"]) if ticket_meta["theme"] else ""
            if "builder" in ticket_meta:
                context["builder"] = str(ticket_meta["builder"]) if ticket_meta["builder"] else ""
            if "match_source" in ticket_meta:
                context["match_source"] = str(ticket_meta["match_source"]) if ticket_meta["match_source"] else ""
            if "full_thread_summary" in ticket_meta:
                context["full_thread_summary"] = str(ticket_meta["full_thread_summary"]) if ticket_meta["full_thread_summary"] else ""
            # Handle typo in field name that exists in ticket_dashboard.py
            elif "full_thread_summary" in ticket_meta:
                context["full_thread_summary"] = str(ticket_meta["full_thread_summary"]) if ticket_meta["full_thread_summary"] else ""
            
            # Search KB with safe error handling
            try:
                kb_match = search_kb_structured(last_msg, retriever, context=context)
                # Ensure kb_match is a dict
                if not isinstance(kb_match, dict):
                    kb_match = {"error": "Invalid KB match format"}
                # Ensure all values are JSON serializable
                for key in list(kb_match.keys()):
                    if kb_match[key] is None:
                        kb_match[key] = ""
            except Exception as e:
                logger.error(f"KB search error: {e}")
                kb_match = {"error": f"KB search failed: {str(e)}"}
            
            # Add to results
            results.append({
                "part": last_msg[:500],  # Limit length for safety
                "match": kb_match
            })
            
            # Build output with safe fallbacks for all fields
            output_data = {
                "customer_name": str(ticket_meta.get("customer", "Customer")),
                "theme": str(ticket_meta.get("theme", "")),
                "builder": str(ticket_meta.get("builder", "")),
                "url": str(ticket_meta.get("user_site", "")),
                "results": results
            }
            
        else:
            logger.info("Processing without ticket metadata")
            
            # Parse the ticket with error handling
            try:
                parser = TicketParser(ticket_text)
                parsed = parser.extract_all()
                if not isinstance(parsed, dict):
                    parsed = {"parts": [ticket_text]}
            except Exception as e:
                logger.error(f"Error parsing ticket: {e}")
                parsed = {"parts": [ticket_text]}
            
            # Process each part with safe iterations
            parts = parsed.get("parts", [])
            if not parts:
                parts = [ticket_text]
            
            for part in parts:
                # Ensure part is a string
                safe_part = str(part) if part else ""
                
                # Create safe context
                context = {}
                if "theme" in parsed and parsed["theme"]:
                    context["theme"] = str(parsed["theme"])
                if "builder" in parsed and parsed["builder"]:
                    context["builder"] = str(parsed["builder"])
                
                # Search KB with safe error handling
                try:
                    kb_match = search_kb_structured(safe_part, retriever, context=context)
                    # Ensure kb_match is a dict
                    if not isinstance(kb_match, dict):
                        kb_match = {"error": "Invalid KB match format"}
                    # Ensure all values are JSON serializable
                    for key in list(kb_match.keys()):
                        if kb_match[key] is None:
                            kb_match[key] = ""
                except Exception as e:
                    logger.error(f"KB search error: {e}")
                    kb_match = {"error": f"KB search failed: {str(e)}"}
                
                # Add to results
                results.append({
                    "part": safe_part[:500],  # Limit length for safety
                    "match": kb_match
                })
            
            # Build output with safe fallbacks
            output_data = {
                "customer_name": str(parsed.get("customer_name", "Customer")),
                "theme": str(parsed.get("theme", "")),
                "builder": str(parsed.get("builder", "")),
                "results": results
            }
        
        # Add additional instructions if provided
        if additional_instructions:
            output_data["additional_instructions"] = str(additional_instructions)
        
        # Serialize to JSON with thorough error handling
        try:
            result_json = json.dumps(output_data, indent=2)
            # Verify the JSON is valid by loading it
            json.loads(result_json)
            return result_json
        except Exception as json_err:
            logger.error(f"JSON serialization error: {str(json_err)}")
            # Critical fallback - ultra-safe minimal JSON
            return json.dumps({
                "error": "JSON serialization failed",
                "results": [{"part": "Error processing ticket", "match": {}}]
            })
    
    except Exception as e:
        logger.error(f"Critical error in process_ticket_research: {str(e)}")
        # Last resort fallback
        return json.dumps({
            "error": f"Critical processing error: {str(e)}",
            "results": [{"part": "Error processing ticket", "match": {}}]
        })