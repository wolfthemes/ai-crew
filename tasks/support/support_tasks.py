from crewai import Task
from agents.support.support_agent import support_agent
from utils.document_loaders import load_guidelines

def create_support_reply_task(ticket_text: str, research_output: str = None, instruction: str = "", ticket_meta: dict = None) -> Task:
    guidelines = load_guidelines()
    
    # Extract ticket segments information as context
    segments_info = ""
    if ticket_meta and "ticket_parts" in ticket_meta and ticket_meta["ticket_parts"]:
        segments_info = "\n## Identified Ticket Issues\n"
        for i, segment in enumerate(ticket_meta["ticket_parts"], 1):
            segments_info += f"{i}. {segment.get('issue', 'No issue text')}\n"
    
    return Task(
        description=f"""
        # Support Reply Task
        
        You are a support expert. Your job is to respond to this customer support ticket:
        {ticket_text}
        
        {segments_info}
        
        ## Guidelines
        {guidelines}
        
        ## Additional Instructions
        {instruction or "No additional instructions provided."}
        
        ## Research Output
        You are provided with pre-processed research output below.
        The ticket has been broken down into distinct issues, and each has been matched against the knowledge base.
        
        If a match starts with "STRICT_RESPONSE:", this means you must use the exact response content as-is — without rewording or paraphrasing it. 
        However, do NOT include the label "STRICT_RESPONSE:" in the final reply. Just use the response body as part of your answer.
        
        === RESEARCH OUTPUT ===
        {research_output}
        
        ## Instructions for Reply
        1. Address each issue identified in the ticket
        2. Use context clues from the full ticket to determine if some issues may have already been resolved
        3. Structure your reply to address each distinct issue clearly
        4. Use ONLY the research data to generate your response
        5. If no match is found for an issue, explain clearly and politely
        6. Ensure your reply flows naturally despite addressing separate issues
        """,
        expected_output = "Support reply formatted in clean HTML, ready for copy-paste into Ticksy.",
        agent=support_agent
    )