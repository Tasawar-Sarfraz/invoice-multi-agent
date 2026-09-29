from crewai import Crew, Process

from agents.agent1_email_classifier import create_email_classifier_agent
from tasks.email_classification_task import create_email_classification_task


def create_invoice_classification_crew():
    email_agent = create_email_classifier_agent()

    email_task = create_email_classification_task(
        email_agent
    )

    crew = Crew(
        agents=[email_agent],
        tasks=[email_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew
