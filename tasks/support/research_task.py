from crewai import Task
from core.research_processor import process_ticket_research
from agents.support.research_agent import research_agent, research_task_prompt

def create_research_task(ticket_text: str, instruction: str = "", ticket_meta: dict = None) -> Task:
    """
    Create a research task that incorporates additional instructions and ticket segments
    This helps ensure KB searches are guided by the instructions and ticket segments
    """
    # Process the research first, outside of the Task
    research_output = process_ticket_research(ticket_text, ticket_meta, instruction)
    
    # Extract ticket segments information for the task description
    segments_info = ""
    if ticket_meta and "ticket_parts" in ticket_meta and ticket_meta["ticket_parts"]:
        segments_info = "\n## Ticket Segments\n"
        for i, segment in enumerate(ticket_meta["ticket_parts"], 1):
            status = "RESOLVED" if segment.get("resolved", False) else "UNRESOLVED"
            segments_info += f"{i}. [{status}] {segment.get('issue', 'No issue text')}\n"
    
    # Create a task description with the research already done
    task_description = f"""
    # Support Research Task
    
    The research has already been completed for this ticket.
    
    ## Original Ticket
    {ticket_text}
    {segments_info}
    
    ## Additional Instructions
    {instruction or "No additional instructions provided."}
    
    ## Research Results
    {research_output}
    
    Please analyze these research results and ensure they properly match the ticket content and segments.
    Pay special attention to any unresolved segments, as they likely need the most support.
    Return the research output as-is unless you find any critical issues.
    """
    
    # Create the task with research output
    task = Task(
        description=task_description,
        expected_output="Structured ticket parts and KB matches.",
        agent=research_agent,
    )

    # Here we fake the task having already run and returned the result
    task._output = {
        "research_output": research_output
    }
    
    return task