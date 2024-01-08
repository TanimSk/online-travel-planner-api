import threading
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from administrator.models import Administrator
from online_travel_backend.settings import DEFAULT_FROM_EMAIL

from agent.models import Agent, Rfq, RfqCategory


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list, sender):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        self.sender = sender
        threading.Thread.__init__(self)

    def run(self):
        msg = EmailMessage(
            self.subject, self.html_content, self.sender, self.recipient_list
        )
        msg.content_subtype = "html"
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
            "travel_date": rfq_instance.travel_date,
            "created_on": rfq_instance.created_on,
            "tracking_id": rfq_instance.tracking_id,
            "rfq_categories": rfq_categories
        },
    )
    text_content = strip_tags(html_content)

    send_html_mail("RFQ Created", text_content, emails, DEFAULT_FROM_EMAIL)
