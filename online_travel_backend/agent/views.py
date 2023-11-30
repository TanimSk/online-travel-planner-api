from dj_rest_auth.registration.views import RegisterView
from .serializers import AgentCustomRegistrationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission

from .serializers import RfqSerializer, QueryServiceSerializer, QueryResultSerializer

# from vendor.serializers import ManageServicesSerializer
from .models import Rfq
from vendor.models import Service


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


# RFQ
class CreateRfqAPI(APIView):
    serializer_class = RfqSerializer
    permission_classes = [AuthenticateOnlyAgent]

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(
            data=request.data, context={"request": request}
        )

        if serialized_data.is_valid(raise_exception=True):
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
    def get(self, request, format=None, *args, **kwargs):
        if request.GET.get("type") == "pending":
            rfq_instances = Rfq.objects.filter(agent=request.user, status="pending")

        elif request.GET.get("type") == "approved":
            rfq_instances = Rfq.objects.filter(agent=request.user, status="approved")

        elif request.GET.get("type") == "declined":
            rfq_instances = Rfq.objects.filter(agent=request.user, status="declined")

        serialized_data = RfqSerializer(rfq_instances, many=True)
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
