import os
from pathlib import Path
from crewai import Crew, Process
from agents.dev.dev_agent import dev_agent
from crewai import Task
from crewai.memory import LongTermMemory
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage

def dev_crew(task: Task) -> Crew:

    base_dir = Path(__file__).resolve().parent.parent  # <- retourne au dossier "ai-crew"
    db_path = base_dir / "data" / "db" / "coding_memory.db"

    return Crew(
        agents=[dev_agent],
        tasks=[task],
        memory=True,
        long_term_memory=LongTermMemory(
            storage=LTMSQLiteStorage(db_path=str(db_path))
        )
    )
    