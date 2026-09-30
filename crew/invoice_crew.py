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

from tools.database_tool import (
    create_approval_token,
)


def create_invoice_processing_crew():

    agent1 = create_email_classifier_agent()

    agent2 = create_invoice_extractor_agent()

    agent3 = create_po_matcher_agent()

    task1 = create_email_classification_task(
        agent1
    )

    task2 = create_invoice_extraction_task(
        agent2,
        task1,
    )

    task3 = create_po_matching_task(
        agent3,
        task2,
    )

    return Crew(
        agents=[
            agent1,
            agent2,
            agent3,
        ],
        tasks=[
            task1,
            task2,
            task3,
        ],
        process=Process.sequential,
        verbose=True,
    )


def create_approval_processing_crew():

    agent4 = create_approval_processor_agent()

    task4 = create_approval_task(
        agent4
    )

    return Crew(
        agents=[
            agent4,
        ],
        tasks=[
            task4,
        ],
        process=Process.sequential,
        verbose=True,
    )


def generate_invoice_approval_token(
    invoice_id: int,
):
    """
    Generate an approval token only for a pending invoice.

    Token generation is deterministic application logic
    and is intentionally kept outside the LLM workflow.
    """

    return create_approval_token(
        invoice_id
    )
