import threading
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from administrator.models import Administrator
from online_travel_backend.settings import DEFAULT_FROM_EMAIL

from agent.models import Agent, Rfq, RfqCategory, RfqService
from datetime import datetime


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list, sender):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        self.sender = sender
        threading.Thread.__init__(self)

    def run(self):
        msg = EmailMessage(self.subject, "Discover", self.sender, self.recipient_list)
        msg.content_subtype = "html"
        msg.body = self.html_content
        msg.send()


def send_html_mail(subject, html_content, recipient_list, sender):
    EmailThread(subject, html_content, recipient_list, sender).start()


# <status>_<email_to>


def rfq_created_admin(rfq_instance):
    agent_instance = Agent.objects.get(agent=rfq_instance.agent)
    rfq_categories = RfqCategory.objects.filter(rfq=rfq_instance)

    emails = list(
        Administrator.objects.filter(administrator__emailaddress__verified=True)
        .values_list("administrator__email", flat=True)
        .distinct()
    )

    html_content = render_to_string(
        "email_notifications/rfq_created.html",
        {
            "customer_name": rfq_instance.customer_name,
            "agent_name": agent_instance.agent_name,
            "agency_name": agent_instance.agency_name,
            "agent_num": agent_instance.mobile_no,
            "customer_address": rfq_instance.customer_address,
            "customer_num": rfq_instance.contact_no,
            "travel_date": datetime.fromisoformat(rfq_instance.travel_date).strftime(
                "%d/%m/%Y %I:%M %p"
            ),
            "created_on": rfq_instance.created_on,
            "tracking_id": rfq_instance.tracking_id,
            "rfq_categories": rfq_categories,
        },
    )

    send_html_mail("RFQ Created", html_content, emails, DEFAULT_FROM_EMAIL)


def rfq_updated_agent(rfq_instance):
    agent_instance = Agent.objects.get(agent=rfq_instance.agent)
    rfq_services = RfqService.objects.filter(rfq=rfq_instance)

    emails = [agent_instance.agent.email]

    html_content = render_to_string(
        "email_notifications/rfq_updated.html",
        {
            "customer_name": rfq_instance.customer_name,
            "customer_address": rfq_instance.customer_address,
            "customer_num": rfq_instance.contact_no,
            "travel_date": datetime.fromisoformat(rfq_instance.travel_date).strftime(
                "%d/%m/%Y %I:%M %p"
            ),
            "created_on": rfq_instance.created_on,
            "tracking_id": rfq_instance.tracking_id,
            "rfq_services": rfq_services,
        },
    )

    send_html_mail("RFQ Created", html_content, emails, DEFAULT_FROM_EMAIL)
