import threading
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# from django.utils.html import strip_tags
from administrator.models import Administrator
from online_travel_backend.settings import DEFAULT_FROM_EMAIL

from agent.models import Agent, Rfq, RfqCategory, RfqService
from customer.models import Customer
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


def rfq_created_admin(rfq_instance, is_customer=False):
    rfq_categories = RfqCategory.objects.filter(rfq=rfq_instance)
    emails = list(
        Administrator.objects.filter(administrator__emailaddress__verified=True)
        .values_list("administrator__email", flat=True)
        .distinct()
    )

    if not is_customer:
        agent_instance = Agent.objects.get(agent=rfq_instance.agent)
        html_content = render_to_string(
            "email_notifications/rfq_created.html",
            {
                "customer_name": rfq_instance.customer_name,
                "agent_name": agent_instance.agent_name,
                "agency_name": agent_instance.agency_name,
                "agent_num": agent_instance.mobile_no,
                "customer_address": rfq_instance.customer_address,
                "customer_num": rfq_instance.contact_no,
                "travel_date": datetime.fromisoformat(
                    str(rfq_instance.travel_date)
                ).strftime("%d/%m/%Y %I:%M %p"),
                "created_on": rfq_instance.created_on,
                "tracking_id": rfq_instance.tracking_id,
                "rfq_categories": rfq_categories,
            },
        )

    else:
        html_content = render_to_string(
            "email_notifications_customer/rfq_created.html",
            {
                "customer_name": rfq_instance.customer_name,
                "customer_address": rfq_instance.customer_address,
                "customer_num": rfq_instance.contact_no,
                "travel_date": datetime.fromisoformat(
                    str(rfq_instance.travel_date)
                ).strftime("%d/%m/%Y %I:%M %p"),
                "created_on": rfq_instance.created_on,
                "tracking_id": rfq_instance.tracking_id,
                "rfq_categories": rfq_categories,
            },
        )

    send_html_mail("RFQ Created", html_content, emails, DEFAULT_FROM_EMAIL)


def rfq_updated_agent(rfq_instance):
    agent_instance = Agent.objects.get(agent=rfq_instance.agent)
    rfq_services = RfqService.objects.filter(rfq_category__rfq=rfq_instance)

    if agent_instance.pseudo_agent:
        emails = [agent_instance.agent.email]

        html_content = render_to_string(
        "email_notifications/rfq_updated.html",
        {
            "customer_name": rfq_instance.customer_name,
            "customer_address": rfq_instance.customer_address,
            "customer_num": rfq_instance.contact_no,
            "travel_date": datetime.fromisoformat(
                str(rfq_instance.travel_date)
            ).strftime("%d/%m/%Y %I:%M %p"),
            "created_on": rfq_instance.created_on,
            "tracking_id": rfq_instance.tracking_id,
            "rfq_services": rfq_services,
        },
    )
    else:
        # B2C
        emails = [Customer.objects.get(customer=rfq_instance.customer).customer.email]
        html_content = render_to_string(
        "email_notifications_customer/rfq_updated.html",
        {
            "customer_name": rfq_instance.customer_name,
            "customer_address": rfq_instance.customer_address,
            "customer_num": rfq_instance.contact_no,
            "travel_date": datetime.fromisoformat(
                str(rfq_instance.travel_date)
            ).strftime("%d/%m/%Y %I:%M %p"),
            "created_on": rfq_instance.created_on,
            "tracking_id": rfq_instance.tracking_id,
            "rfq_services": rfq_services,
        },
    )

    

    send_html_mail("RFQ Updated and Approved", html_content, emails, DEFAULT_FROM_EMAIL)


def rfq_declined_agent(rfq_instance):
    agent_instance = Agent.objects.get(agent=rfq_instance.agent)
    rfq_services = RfqService.objects.filter(rfq_category__rfq=rfq_instance)

    emails = [agent_instance.agent.email]

    html_content = render_to_string(
        "email_notifications/rfq_declined.html",
        {
            "customer_name": rfq_instance.customer_name,
            "customer_address": rfq_instance.customer_address,
            "customer_num": rfq_instance.contact_no,
            "travel_date": datetime.fromisoformat(
                str(rfq_instance.travel_date)
            ).strftime("%d/%m/%Y %I:%M %p"),
            "created_on": rfq_instance.created_on,
            "tracking_id": rfq_instance.tracking_id,
            "rfq_services": rfq_services,
        },
    )

    send_html_mail("RFQ Declined", html_content, emails, DEFAULT_FROM_EMAIL)


def rfq_confirmed_admin(rfq_instance):
    agent_instance = Agent.objects.get(agent=rfq_instance.agent)
    rfq_services = RfqService.objects.filter(rfq_category__rfq=rfq_instance)

    emails = list(
        Administrator.objects.filter(administrator__emailaddress__verified=True)
        .values_list("administrator__email", flat=True)
        .distinct()
    )

    html_content = render_to_string(
        "email_notifications/rfq_confirmed_admin.html",
        {
            "customer_name": rfq_instance.customer_name,
            "customer_address": rfq_instance.customer_address,
            "customer_num": rfq_instance.contact_no,
            "agent_name": agent_instance.agent_name,
            "agency_name": agent_instance.agency_name,
            "agent_num": agent_instance.mobile_no,
            "travel_date": datetime.fromisoformat(
                str(rfq_instance.travel_date)
            ).strftime("%d/%m/%Y %I:%M %p"),
            "created_on": rfq_instance.created_on,
            "tracking_id": rfq_instance.tracking_id,
            "rfq_services": rfq_services,
        },
    )

    send_html_mail("RFQ Confirmed", html_content, emails, DEFAULT_FROM_EMAIL)

    # send email to all vendors
    for service in rfq_services:
        if not service.service.vendor_category.vendor is None:
            html_content = render_to_string(
                "email_notifications/rfq_confirmed_vendor.html",
                {
                    "agent_name": agent_instance.agent_name,
                    "agency_name": agent_instance.agency_name,
                    "agent_num": agent_instance.mobile_no,
                    "travel_date": datetime.fromisoformat(
                        str(rfq_instance.travel_date)
                    ).strftime("%d/%m/%Y %I:%M %p"),
                    "created_on": rfq_instance.created_on,
                    "tracking_id": rfq_instance.tracking_id,
                    "service_category": service.rfq_category.category.category_name,
                    "service_name": service.service.service_name,
                    "service_price": service.service_price,
                },
            )

            send_html_mail(
                "RFQ Confirmed",
                html_content,
                [service.service.vendor_category.vendor.vendor.email],
                DEFAULT_FROM_EMAIL,
            )

    # send email to customer
    html_content = render_to_string(
        "email_notifications/rfq_confirmed_customer.html",
        {
            "agent_name": agent_instance.agent_name,
            "agency_name": agent_instance.agency_name,
            "agent_num": agent_instance.mobile_no,
            "travel_date": datetime.fromisoformat(
                str(rfq_instance.travel_date)
            ).strftime("%d/%m/%Y %I:%M %p"),
            "created_on": rfq_instance.created_on,
            "tracking_id": rfq_instance.tracking_id,
            "rfq_services": rfq_services,
        },
    )

    send_html_mail(
        "RFQ Confirmed", html_content, [rfq_instance.email_address], DEFAULT_FROM_EMAIL
    )
