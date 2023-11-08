from rest_framework.permissions import BasePermission
from dj_rest_auth.registration.views import RegisterView
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.utils import timezone

from .serializers import (
    AdminCustomRegistrationSerializer,
    RfqSerializer,
    RfqApproveSerializer,
)
from commons.serializers import CategorySerializer

from agent.models import Rfq
from commons.models import Category


# Authenticate Vendor Only Class
class AuthenticateOnlyAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_admin:
                return True
            else:
                return False
        return False


# Agent Registration
class AdminRegistrationView(RegisterView):
    serializer_class = AdminCustomRegistrationSerializer


# Pagination Config
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 12
    page_query_param = "p"


class CategoryAPI(APIView):
    serializer_class = CategorySerializer
    permission_classes = [AuthenticateOnlyAdmin]

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = CategorySerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            Category.objects.create(**serialized_data.data)
            return Response({"status": "Successfully created category"})


class PendingRfqAPI(APIView):
    serializer_class = RfqSerializer
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            rfqs_instance = Rfq.objects.filter(status="pending")
            serialized_data = RfqSerializer(rfqs_instance, many=True)
            return Response(serialized_data.data)

        rfqs_instance = get_object_or_404(Rfq, id=rfq_id, status="pending")
        serialized_data = RfqSerializer(rfqs_instance)
        return Response(serialized_data.data)

    def post(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID missing"})

        rfqs_instance = get_object_or_404(Rfq, id=rfq_id)
        serialized_data = RfqApproveSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            if serialized_data.data.get("approved"):
                status = "approved"

            else:
                status = "declined"

            rfqs_instance.status = status
            rfqs_instance.save()

            return Response({"status": f"Successfully {status}"})


# TODO:
# Query service -> select service -> attach to foreign key


class ApprovedRfqAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            rfqs_instance = Rfq.objects.filter(status="approved")
            serialized_data = RfqSerializer(rfqs_instance, many=True)
            return Response(serialized_data.data)

        rfqs_instance = get_object_or_404(Rfq, id=rfq_id, status="approved")
        serialized_data = RfqSerializer(rfqs_instance)
        return Response(serialized_data.data)

    def post(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID missing"})

        rfqs_instance = get_object_or_404(Rfq, id=rfq_id, status="approved")
        rfqs_instance.status = "assigned"
        rfqs_instance.assigned_on = timezone.now()
        rfqs_instance.save()

        return Response({"status": "Successfully assigned to agent"})
