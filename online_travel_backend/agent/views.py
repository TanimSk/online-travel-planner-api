from dj_rest_auth.registration.views import RegisterView
from .serializers import AgentCustomRegistrationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission

from .serializers import (
    RfqSerializer,
    QueryServiceSerializer,
    QueryResultSerializer,
    BillServicesSerializer,
    BillPaySerializer,
    CommissionSerializer,
)

from administrator.serializers import RfqSerializer as RfqInvoiceSerializer

# from vendor.serializers import ManageServicesSerializer
from commons.models import Bill
from .models import Rfq, RfqService, Agent
from vendor.models import Service
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, F
import math


# Authenticate Agent Only Class
class AuthenticateOnlyAgent(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_agent:
                return True
            else:
                return False
        return False


# Agent Registration
class AgentRegistrationView(RegisterView):
    serializer_class = AgentCustomRegistrationSerializer


# Overview
class OverviewAPI(APIView):
    permission_classes = [AuthenticateOnlyAgent]

    def get(self, request, format=None, *args, **kwargs):
        rfqs_instance = Rfq.objects.filter(agent=request.user)

        total_rfq = rfqs_instance.count()
        sent_rfq = (
            rfqs_instance.exclude(status="declined").exclude(status="completed").count()
        )
        cancelled_rfq = rfqs_instance.filter(status="declined").count()
        pending_rfq = rfqs_instance.filter(status="pending").count()
        confirmed_rfq = rfqs_instance.filter(status="confirmed").count()

        completed_rfq = rfqs_instance.filter(status="completed").count()

        return Response(
            {
                "sent_rfqs": sent_rfq,
                "cancelled_rfqs": cancelled_rfq,
                "pending_rfq": pending_rfq,
                "confirmed_rfq": confirmed_rfq,
                "total_rfq": total_rfq,
                "chart": {"completed_rfq": completed_rfq, "incomplete_rfq": sent_rfq},
            }
        )


# RFQ
class CreateRfqAPI(APIView):
    serializer_class = RfqSerializer
    permission_classes = [AuthenticateOnlyAgent]

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(
            data=request.data, context={"request": request, "total_price": False}
        )

        if serialized_data.is_valid(raise_exception=True):
            if request.GET.get("get_price") == "true":
                return Response(serialized_data.calc_total_price(serialized_data.data))

            serialized_data.create(serialized_data.data)
            return Response({"status": "Successfully created RFQ"})


# Query Service
class QueryServicesAPI(APIView):
    permission_classes = [AuthenticateOnlyAgent]
    serializer_class = QueryServiceSerializer

    def get_search_keys(self, data):
        dict = {}
        for key, value in data.items():
            if not (value == "" or value is None):
                dict[f"{key}__icontains"] = value
        return dict

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            # keeping all keys instead of non-search params, for searching
            serialized_copy = serialized_data.data

            for key in [
                "category_id",
                "infant_members",
                "child_members",
                "adult_members",
                "members",
            ]:
                serialized_copy.pop(key)

            services_instances = Service.objects.filter(
                vendor_category__category__id=serialized_data.data.get("category_id"),
                approved=True,
                **self.get_search_keys(serialized_copy),
            )
            serialized_services = QueryResultSerializer(
                services_instances,
                many=True,
                context={"dictionary": serialized_data.data},
            )
            return Response(serialized_services.data)


# RFQ Types
class RFQTypesAPI(APIView):
    permission_classes = [AuthenticateOnlyAgent]

    def get(self, request, format=None, *args, **kwargs):
        has_multiple = False

        if request.GET.get("type") == "order_updates":
            if request.GET.get("id") is not None:
                rfq_instances = Rfq.objects.get(
                    agent=request.user, id=int(request.GET.get("id"))
                ).exclude(status="declined")
            else:
                rfq_instances = Rfq.objects.filter(
                    agent=request.user,
                ).exclude(status="declined")
                has_multiple = True

        elif (
            request.GET.get("type") == "pending"
            or request.GET.get("type") == "approved"
            or request.GET.get("type") == "declined"
            or request.GET.get("type") == "completed"
        ):
            if request.GET.get("id") is not None:
                rfq_instances = Rfq.objects.get(
                    agent=request.user,
                    status=request.GET.get("type"),
                    id=int(request.GET.get("id")),
                )

            else:
                rfq_instances = Rfq.objects.filter(
                    agent=request.user, status=request.GET.get("type")
                ).order_by("-created_on")
                has_multiple = True

        else:
            return Response({"error": "Invalid params"})

        serialized_data = RfqInvoiceSerializer(rfq_instances, many=has_multiple)
        return Response(serialized_data.data)

    def post(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID is missing"})

        rfq_instance = Rfq.objects.get(id=rfq_id)
        rfq_instance.status = "confirmed"
        rfq_instance.save()

        return Response({"status": "Successfully confirmed RFQ"})

    def delete(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID is missing"})

        rfq_instance = Rfq.objects.get(id=rfq_id)
        rfq_instance.delete()

        return Response({"status": "Successfully deleted RFQ"})


# Get Invoice
class GetInvoiceAPI(APIView):
    def get(self, request, rfq_tracing_id=None, format=None, *args, **kwargs):
        if rfq_tracing_id is None:
            if request.user.is_authenticated:
                rfq_instances = Rfq.objects.filter(
                    agent=request.user, status="confirmed"
                )
                serialized_data = RfqSerializer(rfq_instances, many=True)
                return Response(serialized_data.data)

            else:
                return Response({"error": "User is not authenticated"})

        # Send Invoice
        rfq_instance = Rfq.objects.get(tracking_id=rfq_tracing_id)
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
            "invoice.html",
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


# request bill
class RequestBillAPI(APIView):
    permission_classes = [AuthenticateOnlyAgent]

    def get(self, request, format=None, *args, **kwargs):
        if request.GET.get("paid") == "true":
            bills_instance = Bill.objects.filter(
                agent=request.user, status="admin_paid"
            )
        else:
            bills_instance = Bill.objects.filter(
                agent=request.user, status="agent_bill"
            )

        serialized_data = BillServicesSerializer(bills_instance, many=True)
        return Response(serialized_data.data)


class BillPayAPI(APIView):
    permission_classes = [AuthenticateOnlyAgent]

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = BillPaySerializer(data=request.data, many=True)

        if serialized_data.is_valid(raise_exception=True):
            for service in serialized_data.data:
                bill_instance = Bill.objects.get(
                    tracking_id=service.get("tracking_id", None),
                )
                bill_instance.admin_payment_type = service.get(
                    "admin_payment_type", None
                )
                bill_instance.admin_paid_on = timezone.now()
                bill_instance.status = "admin_paid"
                bill_instance.save()

                return Response({"status": "Successfully paid bills"})


class SetCommissionAPI(APIView):
    permission_classes = [AuthenticateOnlyAgent]

    def put(self, request, format=None, *args, **kwargs):
        serialized_data = CommissionSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            agent_instance = Agent.objects.get(agent=request.user)
            agent_instance.commission = serialized_data.data.get("commission")
            agent_instance.save()

            return Response({"status": "Successfully Updated Commission"})

    def get(self, request, format=None, *args, **kwargs):
        agent_instance = Agent.objects.get(agent=request.user)
        return Response({"commission": agent_instance.commission})
