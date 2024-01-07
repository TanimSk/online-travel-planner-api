from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from dj_rest_auth.registration.views import RegisterView
from agent.models import Agent, Rfq, RfqService
from commons.models import Bill

from .serializers import CustomerCustomRegistrationSerializer, RfqSerializer
from administrator.serializers import RfqSerializer as RfqInvoiceSerializer
from django.db import transaction


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

        return Response({"status": "Successfully confirmed RFQ"})

    def delete(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID is missing"})

        rfq_instance = Rfq.objects.get(id=rfq_id, customer=request.user)
        rfq_instance.delete()

        return Response({"status": "Successfully deleted RFQ"})
