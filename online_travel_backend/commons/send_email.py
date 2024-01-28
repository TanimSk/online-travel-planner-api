import threading
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# from django.utils.html import strip_tags
from administrator.serializers import RfqSerializer as RfqInvoiceSerializer
from administrator.models import Administrator
from online_travel_backend.settings import DEFAULT_FROM_EMAIL
from django.db.models import Sum, F
from django.utils import timezone
import math

from agent.models import Agent, Rfq, RfqCategory, RfqService
from customer.models import Customer
from vendor.models import Vendor
from commons.models import AdminSubBill, AgentSubBill
from datetime import datetime
from weasyprint import HTML


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list, sender, pdfs=None):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        self.sender = sender
        self.pdfs = pdfs
        threading.Thread.__init__(self)

    def run(self):
        msg = EmailMessage(self.subject, None, self.sender, self.recipient_list)

        # sending PDFs
        if self.pdfs is not None:
            for pdf in self.pdfs:
                pdf_data = HTML(string=pdf["content"]).write_pdf()
                msg.attach(pdf["name"], pdf_data, "application/pdf")

        msg.content_subtype = "html"
        msg.body = self.html_content
        msg.send()


def send_html_mail(subject, html_content, recipient_list, sender, pdfs=None):
    EmailThread(subject, html_content, recipient_list, sender, pdfs).start()


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

        html_content_agent = render_to_string(
            "email_notifications/rfq_created_agent.html",
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

        # send to agent
        send_html_mail(
            "RFQ Created",
            html_content_agent,
            [rfq_instance.agent.email],
            DEFAULT_FROM_EMAIL,
            # [{"name": "test.pdf", "content": html_content}],
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

    # send to admin
    send_html_mail("RFQ Created", html_content, emails, DEFAULT_FROM_EMAIL)


def rfq_updated_agent(rfq_instance):
    agent_instance = Agent.objects.get(agent=rfq_instance.agent)
    rfq_services = RfqService.objects.filter(rfq_category__rfq=rfq_instance)

    if not agent_instance.pseudo_agent:
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

    if not agent_instance.pseudo_agent:
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
    else:
        emails = [Customer.objects.get(customer=rfq_instance.customer).customer.email]

        html_content = render_to_string(
            "email_notifications_customer/rfq_declined.html",
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


def generate_invoice(rfq_instance, services_instance, is_customer):
    # Calculation
    total_service_charge = services_instance.aggregate(Sum("service_price"))[
        "service_price__sum"
    ]
    extra_charge_admin = services_instance.aggregate(
        charge=Sum((F("service_price") * F("admin_commission")) / 100)
    )["charge"]
    extra_charge_agent = services_instance.aggregate(
        charge=Sum((F("service_price") * F("agent_commission")) / 100)
    )["charge"]

    serialized_data = RfqInvoiceSerializer(rfq_instance)

    if not is_customer:
        return render_to_string(
            "agent/invoice.html",
            {
                "data": serialized_data.data,
                "today_date": timezone.now(),
                "total_charge": math.ceil(total_service_charge),
                "extra_charge": math.ceil(extra_charge_admin + extra_charge_agent),
                "total_price": math.ceil(
                    total_service_charge + extra_charge_agent + extra_charge_admin
                ),
            },
        )

    else:
        return render_to_string(
            "customer/invoice.html",
            {
                "data": serialized_data.data,
                "today_date": timezone.now(),
                "total_charge": math.ceil(total_service_charge),
                "extra_charge": math.ceil(extra_charge_admin + extra_charge_agent),
                "total_price": math.ceil(
                    total_service_charge + extra_charge_agent + extra_charge_admin
                ),
            },
        )


def rfq_confirmed_admin(rfq_instance, is_customer=False):
    rfq_services = RfqService.objects.filter(rfq_category__rfq=rfq_instance)
    emails = list(
        Administrator.objects.filter(administrator__emailaddress__verified=True)
        .values_list("administrator__email", flat=True)
        .distinct()
    )

    # send emails to admin
    if not is_customer:
        agent_instance = Agent.objects.get(agent=rfq_instance.agent)

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
    else:
        html_content = render_to_string(
            "email_notifications_customer/rfq_confirmed_admin.html",
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

    send_html_mail("RFQ Confirmed", html_content, emails, DEFAULT_FROM_EMAIL)

    # send email to all vendors
    for service in rfq_services:
        if not service.service.vendor_category.vendor is None:
            if not is_customer:
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
            else:
                html_content = render_to_string(
                    "email_notifications_customer/rfq_confirmed_vendor.html",
                    {
                        "customer_name": rfq_instance.customer_name,
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
    if not is_customer:
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

        # services pdfs
        services_pdf_array = []

        for rfq_service in rfq_services:
            services_pdf_array.append(
                {
                    "name": f"{rfq_service.service.service_name}.pdf",
                    "content": render_to_string(
                        "email_notifications/pdfs/rfq_confirmed_customer.html",
                        {
                            "agency_name": agent_instance.agency_name,
                            "logo_url": agent_instance.logo_url,
                            "rfq_service": rfq_service,
                        },
                    ),
                }
            )

        services_pdf_array.append(
            {
                "name": f"Invoice-{timezone.now().strftime('%d/%m/%Y-%H-%M-%S')}.pdf",
                "content": generate_invoice(rfq_instance, rfq_services, is_customer),
            }
        )

    else:
        html_content = render_to_string(
            "email_notifications_customer/rfq_confirmed_customer.html",
            {
                "travel_date": datetime.fromisoformat(
                    str(rfq_instance.travel_date)
                ).strftime("%d/%m/%Y %I:%M %p"),
                "created_on": rfq_instance.created_on,
                "tracking_id": rfq_instance.tracking_id,
                "rfq_services": rfq_services,
            },
        )

        # services pdfs
        services_pdf_array = []

        for rfq_service in rfq_services:
            services_pdf_array.append(
                {
                    "name": f"{rfq_service.service.service_name}.pdf",
                    "content": render_to_string(
                        "email_notifications_customer/pdfs/rfq_confirmed_customer.html",
                        {
                            "rfq_service": rfq_service,
                        },
                    ),
                }
            )

        services_pdf_array.append(
            {
                "name": f"Invoice-{timezone.now().strftime('%d/%m/%Y-%H-%M-%S')}.pdf",
                "content": generate_invoice(rfq_instance, rfq_services, is_customer),
            }
        )

    send_html_mail(
        "RFQ Confirmed",
        html_content,
        [rfq_instance.email_address],
        DEFAULT_FROM_EMAIL,
        pdfs=services_pdf_array,
    )


# rfq_assigned_vendor.html
def rfq_assigned_vendor(service_instance):
    agent_instance = Agent.objects.get(agent=service_instance.rfq_category.rfq.agent)

    html_content = render_to_string(
        "email_notifications/rfq_assigned_vendor.html",
        {
            "agent_name": agent_instance.agent_name,
            "agency_name": agent_instance.agency_name,
            "agent_num": agent_instance.mobile_no,
            "service_category": service_instance.rfq_category.category.category_name,
            "service_name": service_instance.service.service_name,
            "service_price": service_instance.service_price,
        },
    )
    send_html_mail(
        "RFQ Assigned",
        html_content,
        [service_instance.service.vendor_category.vendor.vendor.email],
        DEFAULT_FROM_EMAIL,
    )


def bill_request_agent(bill_instance):
    agent_instance = Agent.objects.get(agent=bill_instance.agent)

    # Send to agent
    if not agent_instance.pseudo_agent:
        emails = [bill_instance.agent.email]

        html_content = render_to_string(
            "email_notifications/bill_request_agent.html",
            {
                "bill_instance": bill_instance,
                "travel_date": datetime.fromisoformat(
                    str(bill_instance.service.rfq_category.rfq.travel_date)
                ).strftime("%d/%m/%Y %I:%M %p"),
                "created_on": bill_instance.service.rfq_category.rfq.created_on,
                "tracking_id": bill_instance.service.rfq_category.rfq.tracking_id,
                "customer_name": bill_instance.service.rfq_category.rfq.customer_name,
                "customer_address": bill_instance.service.rfq_category.rfq.customer_address,
                "customer_num": bill_instance.service.rfq_category.rfq.contact_no,
            },
        )
    else:
        # Send to customer
        emails = [bill_instance.service.rfq_category.rfq.email_address]

        html_content = render_to_string(
            "email_notifications_customer/bill_request_agent.html",
            {
                "bill_instance": bill_instance,
                "travel_date": datetime.fromisoformat(
                    str(bill_instance.service.rfq_category.rfq.travel_date)
                ).strftime("%d/%m/%Y %I:%M %p"),
                "created_on": bill_instance.service.rfq_category.rfq.created_on,
                "tracking_id": bill_instance.service.rfq_category.rfq.tracking_id,
            },
        )
    send_html_mail(
        "Bill Requested - Discover Thailand", html_content, emails, DEFAULT_FROM_EMAIL
    )


def bill_pay_admin(bill_instance, is_customer=False):
    agent_instance = Agent.objects.get(agent=bill_instance.agent)
    emails = list(
        Administrator.objects.filter(administrator__emailaddress__verified=True)
        .values_list("administrator__email", flat=True)
        .distinct()
    )

    if not is_customer:
        html_content = render_to_string(
            "email_notifications/bill_pay_admin.html",
            {
                "agent_name": agent_instance.agent_name,
                "agency_name": agent_instance.agency_name,
                "agent_num": agent_instance.mobile_no,
                "bill_instance": bill_instance,
                "paid_amount": bill_instance.admin_bill
                + bill_instance.vendor_bill
                - bill_instance.agent_due,
                "travel_date": datetime.fromisoformat(
                    str(bill_instance.service.rfq_category.rfq.travel_date)
                ).strftime("%d/%m/%Y %I:%M %p"),
                "created_on": bill_instance.service.rfq_category.rfq.created_on,
                "tracking_id": bill_instance.service.rfq_category.rfq.tracking_id,
                "customer_name": bill_instance.service.rfq_category.rfq.customer_name,
                "customer_address": bill_instance.service.rfq_category.rfq.customer_address,
                "customer_num": bill_instance.service.rfq_category.rfq.contact_no,
            },
        )

        # pdf
        latest_bill = (
            AgentSubBill.objects.filter(bill=bill_instance).order_by("-paid_on").first()
        )

        html_pdf_array = [
            {
                "name": f"Agent-paid-{timezone.now().strftime('%d/%m/%Y-%H-%M-%S')}",
                "content": render_to_string(
                    "email_notifications/pdfs/bill_pay_admin.html",
                    {
                        "logo_url": agent_instance.logo_url,
                        "agent_name": agent_instance.agent_name,
                        "agency_name": agent_instance.agency_name,
                        "agent_num": agent_instance.mobile_no,
                        "agent_address": agent_instance.agent_address,
                        "bill_instance": bill_instance,
                        "paid_amount": latest_bill.paid_amount,
                        "t_paid_amount": bill_instance.admin_bill
                        + bill_instance.vendor_bill
                        - bill_instance.agent_due,
                        "paid_by": latest_bill.payment_type,
                        "receipt_img": latest_bill.receipt_img,
                        "received_by": latest_bill.received_by,
                    },
                ),
            }
        ]

    else:
        html_content = render_to_string(
            "email_notifications_customer/bill_pay_admin.html",
            {
                "bill_instance": bill_instance,
                "paid_amount": bill_instance.admin_bill
                + bill_instance.vendor_bill
                - bill_instance.agent_due,
                "travel_date": datetime.fromisoformat(
                    str(bill_instance.service.rfq_category.rfq.travel_date)
                ).strftime("%d/%m/%Y %I:%M %p"),
                "created_on": bill_instance.service.rfq_category.rfq.created_on,
                "tracking_id": bill_instance.service.rfq_category.rfq.tracking_id,
                "customer_name": bill_instance.service.rfq_category.rfq.customer_name,
                "customer_address": bill_instance.service.rfq_category.rfq.customer_address,
                "customer_num": bill_instance.service.rfq_category.rfq.contact_no,
            },
        )

        # pdf
        latest_bill = (
            AgentSubBill.objects.filter(bill=bill_instance).order_by("-paid_on").first()
        )

        customer_instance = Customer.objects.get(customer=bill_instance.customer)

        html_pdf_array = [
            {
                "name": f"Customer-paid-{timezone.now().strftime('%d/%m/%Y-%H-%M-%S')}",
                "content": render_to_string(
                    "email_notifications_customer/pdfs/bill_pay_admin.html",
                    {
                        "customer": customer_instance,
                        "bill_instance": bill_instance,
                        "paid_amount": latest_bill.paid_amount,
                        "t_paid_amount": bill_instance.admin_bill
                        + bill_instance.vendor_bill
                        - bill_instance.agent_due,
                        "paid_by": latest_bill.payment_type,
                        "receipt_img": latest_bill.receipt_img,
                        "received_by": latest_bill.received_by,
                    },
                ),
            }
        ]

    send_html_mail(
        "Bill Paid", html_content, emails, DEFAULT_FROM_EMAIL, html_pdf_array
    )


def bill_request_admin(bill_instance):
    emails = list(
        Administrator.objects.filter(administrator__emailaddress__verified=True)
        .values_list("administrator__email", flat=True)
        .distinct()
    )

    vendor_instance = Vendor.objects.get(vendor=bill_instance.vendor)

    html_content = render_to_string(
        "email_notifications/bill_req_admin.html",
        {
            "vendor_name": vendor_instance.vendor_name,
            "bill_instance": bill_instance,
            "contact_name": vendor_instance.contact_name,
            "vendor_address": vendor_instance.vendor_address,
            "vendor_number": vendor_instance.vendor_name,
            "travel_date": datetime.fromisoformat(
                str(bill_instance.service.rfq_category.rfq.travel_date)
            ).strftime("%d/%m/%Y %I:%M %p"),
            "tracking_id": bill_instance.service.rfq_category.rfq.tracking_id,
        },
    )

    send_html_mail("Bill Requested", html_content, emails, DEFAULT_FROM_EMAIL)


def bill_pay_vendor(bill_instance):
    html_content = render_to_string(
        "email_notifications/bill_pay_vendor.html",
        {
            "bill_instance": bill_instance,
            "amount_paid": bill_instance.vendor_bill - bill_instance.admin_due,
            "travel_date": datetime.fromisoformat(
                str(bill_instance.service.rfq_category.rfq.travel_date)
            ).strftime("%d/%m/%Y %I:%M %p"),
            "tracking_id": bill_instance.service.rfq_category.rfq.tracking_id,
        },
    )

    # pdf
    latest_bill = (
        AdminSubBill.objects.filter(bill=bill_instance).order_by("-paid_on").first()
    )
    vendor_instance = Vendor.objects.get(vendor=bill_instance.vendor)

    html_pdf_array = [
        {
            "name": f"Admin-paid-{timezone.now().strftime('%d/%m/%Y-%H-%M-%S')}",
            "content": render_to_string(
                "email_notifications/pdfs/bill_pay_vendor.html",
                {
                    "vendor": vendor_instance,
                    "bill_instance": bill_instance,
                    "paid_amount": latest_bill.paid_amount,
                    "t_paid_amount": bill_instance.vendor_bill
                    - bill_instance.admin_due,
                    "paid_by": latest_bill.payment_type,
                    "receipt_img": latest_bill.receipt_img,
                    "received_by": latest_bill.received_by,
                },
            ),
        }
    ]

    send_html_mail(
        "Bill Paid",
        html_content,
        [bill_instance.vendor.email],
        DEFAULT_FROM_EMAIL,
        html_pdf_array,
    )


def service_created_admin(service_instance):
    emails = list(
        Administrator.objects.filter(administrator__emailaddress__verified=True)
        .values_list("administrator__email", flat=True)
        .distinct()
    )

    html_content = render_to_string(
        "email_notifications/service_created_admin.html",
        {
            "vendor_name": service_instance.vendor_category.vendor.vendor_name,
            "vendor_address": service_instance.vendor_category.vendor.vendor_address,
            "vendor_number": service_instance.vendor_category.vendor.vendor_number,
            "category_name": service_instance.vendor_category.category.category_name,
            "service_name": service_instance.service_name,
            "description": service_instance.description,
        },
    )

    send_html_mail("New Service Created", html_content, emails, DEFAULT_FROM_EMAIL)


def service_approved_vendor(service_instance):
    html_content = render_to_string(
        "email_notifications/service_approved_vendor.html",
        {
            "category_name": service_instance.vendor_category.category.category_name,
            "service_name": service_instance.service_name,
            "description": service_instance.description,
            "created_on": service_instance.created_on,
        },
    )

    send_html_mail(
        "Service Approved",
        html_content,
        [service_instance.vendor_category.vendor.vendor.email],
        DEFAULT_FROM_EMAIL,
    )


def service_declined_vendor(service_instance):
    html_content = render_to_string(
        "email_notifications/service_declined_vendor.html",
        {
            "category_name": service_instance.vendor_category.category.category_name,
            "service_name": service_instance.service_name,
            "description": service_instance.description,
            "created_on": service_instance.created_on,
        },
    )

    send_html_mail(
        "Service Declined",
        html_content,
        [service_instance.vendor_category.vendor.vendor.email],
        DEFAULT_FROM_EMAIL,
    )
