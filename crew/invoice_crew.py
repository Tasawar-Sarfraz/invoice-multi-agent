from crewai import Crew, Process

from agents.agent1_email_classifier import (
    create_email_classifier_agent,
)
from agents.agent2_invoice_extractor import (
    create_invoice_extractor_agent,
)
from agents.agent3_po_matcher import (
    create_po_matcher_agent,
)
from agents.agent4_approval_processor import (
    create_approval_processor_agent,
)

from tasks.email_classification_task import (
    create_email_classification_task,
)
from tasks.invoice_extraction_task import (
    create_invoice_extraction_task,
)
from tasks.po_matching_task import (
    create_po_matching_task,
)
from tasks.approval_task import (
    create_approval_task,
)


def create_invoice_processing_crew():

    agent1 = create_email_classifier_agent()
    agent2 = create_invoice_extractor_agent()
    agent3 = create_po_matcher_agent()
    agent4 = create_approval_processor_agent()

    task1 = create_email_classification_task(agent1)
    task2 = create_invoice_extraction_task(agent2)
    task3 = create_po_matching_task(agent3)
    task4 = create_approval_task(agent4)

    crew = Crew(
        agents=[
            agent1,
            agent2,
            agent3,
            agent4,
        ],
        tasks=[
            task1,
            task2,
            task3,
            task4,
        ],
        process=Process.sequential,
        verbose=True,
    )

    return crew
