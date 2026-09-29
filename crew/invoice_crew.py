from crewai import Crew, Process

from agents.agent1_email_classifier import create_email_classifier_agent
from agents.agent2_invoice_extractor import create_invoice_extractor_agent
from agents.agent3_po_matcher import create_po_matcher_agent
from agents.agent4_approval_processor import create_approval_processor_agent

from tasks.email_classification_task import create_email_classification_task
from tasks.invoice_extraction_task import create_invoice_extraction_task
from tasks.po_matching_task import create_po_matching_task
from tasks.approval_task import create_approval_task


def create_invoice_classification_crew():
    agent = create_email_classifier_agent()
    task = create_email_classification_task(agent)

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )


def create_invoice_extraction_crew():
    agent = create_invoice_extractor_agent()
    task = create_invoice_extraction_task(agent)

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )


def create_po_matching_crew():
    agent = create_po_matcher_agent()
    task = create_po_matching_task(agent)

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )


def create_approval_processing_crew():
    agent = create_approval_processor_agent()
    task = create_approval_task(agent)

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
