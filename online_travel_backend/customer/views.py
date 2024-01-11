from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from dj_rest_auth.registration.views import RegisterView
from agent.models import Agent, Rfq, RfqService
from commons.models import Bill
from .models import Customer

from .serializers import (
    CustomerCustomRegistrationSerializer,
    RfqSerializer,
    ProfileSerializer,
)
from agent.serializers import (
    PaidBillSerializer,
    BillRequestSerializer,
    BillPaySerializer,
)
from administrator.serializers import RfqSerializer as RfqInvoiceSerializer
from commons.send_email import rfq_created_admin, rfq_confirmed_admin, bill_pay_admin
from django.db import transaction

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, F
import math


# Authenticate Agent Only Class
class AuthenticateOnlyCustomer(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_customer:
                return True
            else:
                return False
        return False


# Agent Registration
class CustomerRegistrationView(RegisterView):
    serializer_class = CustomerCustomRegistrationSerializer


# Create RFQ
class CreateRfqAPI(APIView):
    serializer_class = RfqSerializer
    permission_classes = [AuthenticateOnlyCustomer]

    def post(self, request, format=None, *args, **kwargs):
        agent_instance = Agent.objects.filter(pseudo_agent=True).order_by("id").first()

        if agent_instance is None:
            return Response(
                {
                    "error": "Customer pseudo agent not created, please contact the developers"
                }
            )

        serialized_data = self.serializer_class(
            data=request.data,
            context={"request": request, "total_price": False, "agent": agent_instance},
        )

        if serialized_data.is_valid(raise_exception=True):
            if request.GET.get("get_price") == "true":
                return Response(serialized_data.calc_total_price(serialized_data.data))

            rfq_instance = serialized_data.create(serialized_data.data)
            rfq_instance.save()

            rfq_created_admin(rfq_instance=rfq_instance, is_customer=True)
            return Response({"status": "Successfully created RFQ"})


# RFQ Types
class RFQTypesAPI(APIView):
    permission_classes = [AuthenticateOnlyCustomer]

    def get(self, request, format=None, *args, **kwargs):
        has_multiple = False

        if request.GET.get("type") == "order_updates":
            if request.GET.get("id") is not None:
                rfq_instances = Rfq.objects.get(
                    customer=request.user, id=int(request.GET.get("id"))
                )
            else:
                rfq_instances = (
                    Rfq.objects.filter(
                        customer=request.user,
                    )
                    .exclude(status="declined")
                    .order_by("-created_on")
                )
                has_multiple = True

        elif (
            request.GET.get("type") == "pending"
            or request.GET.get("type") == "approved"
            or request.GET.get("type") == "declined"
            or request.GET.get("type") == "completed"
        ):
            if request.GET.get("id") is not None:
                rfq_instances = Rfq.objects.get(
                    customer=request.user,
                    status=request.GET.get("type"),
                    id=int(request.GET.get("id")),
                )

            else:
                rfq_instances = Rfq.objects.filter(
                    customer=request.user, status=request.GET.get("type")
                ).order_by("-created_on")
                has_multiple = True

        else:
            return Response({"error": "Invalid params"})

        serialized_data = RfqInvoiceSerializer(rfq_instances, many=has_multiple)
        return Response(serialized_data.data)

    def post(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID is missing"})

        with transaction.atomic():
            rfq_instance = Rfq.objects.get(id=rfq_id, customer=request.user)
            rfq_instance.status = "confirmed"
            rfq_instance.save()

            rfq_service_instances = RfqService.objects.filter(
                rfq_category__rfq=rfq_instance
            )

            # Calculate & Make Bill for each rfq_services after confirming RFQ
            for rfq_service_instance in rfq_service_instances:
                vendor_ref = {}

                if not rfq_service_instance.service.added_by_admin:
                    vendor_ref = {
                        "vendor": rfq_service_instance.service.vendor_category.vendor.vendor
                    }

                # making bills
                admin_commission = rfq_service_instance.admin_commission * 0.01
                agent_commission = rfq_service_instance.agent_commission * 0.01

                Bill.objects.create(
                    **vendor_ref,
                    agent=rfq_service_instance.rfq_category.rfq.agent,
                    vendor_bill=rfq_service_instance.service_price,
                    admin_bill=rfq_service_instance.service_price * admin_commission,
                    agent_bill=rfq_service_instance.service_price * agent_commission,
                    agent_due=(rfq_service_instance.service_price * admin_commission)
                    + rfq_service_instance.service_price,
                    admin_due=rfq_service_instance.service_price,
                    service=rfq_service_instance,
                )

            rfq_confirmed_admin(rfq_instance, is_customer=True)

        return Response({"status": "Successfully confirmed RFQ"})

    def delete(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID is missing"})

        rfq_instance = Rfq.objects.get(id=rfq_id, customer=request.user)
        rfq_instance.delete()

        return Response({"status": "Successfully deleted RFQ"})


# Get Invoice
class GetInvoiceAPI(APIView):
    def get(self, request, rfq_tracing_id=None, format=None, *args, **kwargs):
        if rfq_tracing_id is None:
            if request.user.is_authenticated:
                rfq_instances = Rfq.objects.filter(
                    customer=request.user, status="confirmed"
                ).order_by("-created_on")
                serialized_data = RfqInvoiceSerializer(rfq_instances, many=True)
                return Response(serialized_data.data)

            else:
                return Response({"error": "User is not authenticated"})

        # Send Invoice
        rfq_instance = Rfq.objects.get(
            tracking_id=rfq_tracing_id,
            # customer=request.user
        )
        services_instance = RfqService.objects.filter(rfq_category__rfq=rfq_instance)

        # Calculation
        total_service_charge = services_instance.aggregate(Sum("service_price"))[
            "service_price__sum"
        ]
        extra_charge_admin = services_instance.aggregate(
            charge=Sum((F("service_price") * F("admin_commission")) / 100)
        )["charge"]
        extra_charge_agent = services_instance.aggregate(
            charge=Sum((F("service_price") * F("admin_commission")) / 100)
        )["charge"]

        serialized_data = RfqInvoiceSerializer(rfq_instance)
        return render(
            request,
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


class AgentBillsAPI(APIView):
    permission_classes = [AuthenticateOnlyCustomer]

    def get(self, request, format=None, *args, **kwargs):
        agent_instance = Agent.objects.filter(pseudo_agent=True).order_by("id").first()

        if agent_instance is None:
            return Response(
                {
                    "error": "Customer pseudo agent not created, please contact the developers"
                }
            )

        if request.GET.get("paid") == "true":
            # list of paid bills
            bills_instance = Bill.objects.filter(
                agent=agent_instance.agent,
                status_1="admin_paid",
                service__rfq_category__rfq__customer=request.user,
            ).order_by("-admin_paid_on")
            serialized_data = PaidBillSerializer(bills_instance, many=True)
            return Response(serialized_data.data)

        # list of bill requests with due payment
        bills_instance = (
            Bill.objects.filter(
                agent=agent_instance.agent,
                agent_due__gt=0,
                service__rfq_category__rfq__customer=request.user,
            )
            .exclude(status_1="admin_bill")
            .order_by("-agent_billed_on")
        )
        serialized_data = BillRequestSerializer(bills_instance, many=True)
        return Response(serialized_data.data)

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = BillPaySerializer(data=request.data, many=True)

        if serialized_data.is_valid(raise_exception=True):
            for service in serialized_data.data:
                bill_instance = Bill.objects.get(
                    tracking_id=service.get("tracking_id", None),
                )
                due_amount = (
                    # bill_instance.vendor_bill
                    # + bill_instance.agent_bill
                    +bill_instance.agent_due
                    - service.get("paid_amount")
                )

                if due_amount < 0:
                    return Response(
                        {"error": "Paid amount cannot be greater than bill!"}
                    )

                bill_instance.admin_payment_type = service.get(
                    "admin_payment_type", None
                )
                bill_instance.agent_due = due_amount
                bill_instance.admin_paid_on = timezone.now()
                bill_instance.status_1 = "admin_paid"
                bill_instance.save()

                bill_pay_admin(bill_instance=bill_instance, is_customer=True)

                return Response({"status": "Successfully paid bills"})


class ProfileAPI(APIView):
    permission_classes = [AuthenticateOnlyCustomer]
    serializer_class = ProfileSerializer

    def get(self, request, format=None, *args, **kwargs):
        customer_instance = Customer.objects.get(customer=request.user)
        serialized_data = self.serializer_class(customer_instance)
        return Response(serialized_data.data)

    def put(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            Customer.objects.filter(customer=request.user).update(
                **serialized_data.data
            )
            return Response({"status": "Successfully updated"})
