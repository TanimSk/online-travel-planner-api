from dj_rest_auth.registration.views import RegisterView
from .serializers import AgentCustomRegistrationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission

from .serializers import RfqSerializer, QueryServiceSerializer
from vendor.serializers import ManageServicesSerializer
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

    def get(self, request, format=None, *args, **kwargs):
        return Response(RfqSerializer(Rfq.objects.all(), many=True).data)

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
            # keeping all keys instead of category_id, for searching
            serialized_copy = serialized_data.data
            serialized_copy.pop("category_id")

            services_instances = Service.objects.filter(
                vendor_category__category__id=serialized_data.data.get("category_id"),
                approved=True,
                **self.get_search_keys(serialized_copy),
            )
            serialized_services = ManageServicesSerializer(
                services_instances, many=True
            )
            return Response(serialized_services.data)
