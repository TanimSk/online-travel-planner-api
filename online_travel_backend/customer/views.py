from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from dj_rest_auth.registration.views import RegisterView
from agent.models import Agent, Rfq
from .serializers import CustomerCustomRegistrationSerializer, RfqSerializer
from administrator.serializers import RfqSerializer as RfqInvoiceSerializer


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
