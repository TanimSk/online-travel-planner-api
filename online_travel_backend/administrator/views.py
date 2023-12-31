from rest_framework.permissions import BasePermission
from dj_rest_auth.registration.views import RegisterView
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone

from .serializers import (
    AdminCustomRegistrationSerializer,
    RfqSerializer,
    ApprovalSerializer,
    VendorListSerializer,
    BasicRfqSerializer,
    AssignServiceSerializer,
    AdminDispatchBillSerializer,
)
from commons.serializers import CategorySerializer
from vendor.serializers import (
    RfqServiceSerializer,
    ManageServicesSerializer,
    BillServicesSerializer,
)

from agent.models import Rfq, RfqService
from commons.models import Category, User
from vendor.models import Vendor, VendorCategory, Service


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
            rfqs_instance = Rfq.objects.filter(status="pending").order_by("-created_on")
            serialized_data = RfqSerializer(rfqs_instance, many=True)
            return Response(serialized_data.data)

        rfqs_instance = get_object_or_404(Rfq, id=rfq_id, status="pending")
        serialized_data = RfqSerializer(rfqs_instance)
        return Response(serialized_data.data)

    def post(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID missing"})

        rfqs_instance = get_object_or_404(Rfq, id=rfq_id)
        serialized_data = ApprovalSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            if serialized_data.data.get("approved"):
                status = "approved"

            else:
                status = "declined"

            rfqs_instance.status = status
            rfqs_instance.approved_on = timezone.now()
            rfqs_instance.save()

            return Response({"status": f"Successfully {status}"})


# TODO:
# Query service -> select service -> attach to foreign key


class ApprovedRfqAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            rfqs_instance = Rfq.objects.filter(status="approved").order_by(
                "-created_on"
            )
            serialized_data = RfqSerializer(rfqs_instance, many=True)
            return Response(serialized_data.data)

        rfqs_instance = get_object_or_404(Rfq, id=rfq_id, status="approved")
        serialized_data = RfqSerializer(rfqs_instance)
        return Response(serialized_data.data)


# Manage Vendors
class VendorListAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, vendor_id=None, format=None, *args, **kwargs):
        if vendor_id is None:
            vendor_instances = Vendor.objects.filter(approved=True).order_by(
                "-added_on"
            )
            serialized_data = VendorListSerializer(vendor_instances, many=True)
        else:
            vendor_instances = Vendor.objects.get(id=vendor_id, approved=True)
            serialized_data = VendorListSerializer(vendor_instances)

        return Response(serialized_data.data)


# Get, approve and delete requested vendors
class RequestedVendorAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, vendor_id=None, format=None, *args, **kwargs):
        if vendor_id is None:
            vendor_instances = Vendor.objects.filter(approved=False).order_by(
                "-added_on"
            )
            serialized_data = VendorListSerializer(vendor_instances, many=True)
        else:
            vendor_instances = get_object_or_404(Vendor, id=vendor_id, approved=False)
            serialized_data = VendorListSerializer(vendor_instances)

        return Response(serialized_data.data)

    def post(self, request, vendor_id=None, format=None, *args, **kwargs):
        if vendor_id is None:
            return Response({"error": "Vendor id missing"})

        vendor_instance = get_object_or_404(Vendor, id=vendor_id, approved=False)
        vendor_instance.approved = True
        vendor_instance.save()
        return Response({"status": "Successfully approved"})

    def delete(self, request, vendor_id=None, format=None, *args, **kwargs):
        if vendor_id is None:
            return Response({"error": "Vendor id missing"})

        vendor_instance = get_object_or_404(Vendor, id=vendor_id, approved=False)
        get_object_or_404(User, vendor=vendor_instance).delete()
        return Response({"status": "Successfully removed vendor"})


class TaskListAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, format=None, *args, **kwargs):
        rfq_instances = (
            Rfq.objects.filter(
                status="assigned",
            )
            .distinct()
            .order_by("-assigned_on")
        )

        response_arr = []
        for rfq_instance in rfq_instances:
            obj_data = {}
            obj_data["rfq_details"] = RfqSerializer(rfq_instance).data

            services_instance = RfqService.objects.filter(
                rfq_category__rfq=rfq_instance
            )
            serialized_data = RfqServiceSerializer(services_instance, many=True)
            obj_data["services_details"] = serialized_data.data

            response_arr.append(obj_data)

        return Response(response_arr)


# --------------- Manage Services ---------------
# vendor services
# approve service, view unapproved/approved service,
class ManageVendorServicesAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]
    serializer_class = ManageServicesSerializer

    def get(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            approved = True if request.GET.get("approved") == "true" else False
            instance = Service.objects.filter(approved=approved, added_by_admin=False)
            serialized_data = self.serializer_class(instance, many=True)
            return Response(serialized_data.data)

        try:
            instance = Service.objects.get(id=service_id, added_by_admin=False)
            serialized_data = self.serializer_class(instance)

        except Service.DoesNotExist:
            return Response({"error": "Service not found"})

        return Response(serialized_data.data)

    def post(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            return Response({"error": "Service id is missing"})

        instance = Service.objects.get(id=service_id, added_by_admin=False)
        instance.approved = True
        instance.save()
        return Response({"status": "Service has been approved"})


# admin services
class ManageServicesAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]
    serializer_class = ManageServicesSerializer

    def get(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            instance = Service.objects.filter(added_by_admin=True)
            serialized_data = self.serializer_class(instance, many=True)
            return Response(serialized_data.data)
        try:
            instance = Service.objects.get(id=service_id, added_by_admin=True)
            serialized_data = self.serializer_class(instance)

        except Service.DoesNotExist:
            return Response({"error": "Service not found"})

        return Response(serialized_data.data)

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            service_data = serialized_data.data
            service_data.pop("category_id")
            category_id = serialized_data.data.get("category_id")

            # Check if Category exists
            if Category.objects.filter(id=category_id).exists():
                # Creating a category for a admin service (for tracing)
                vendor_category_instance = VendorCategory.objects.create(
                    category_id=category_id
                )
                Service.objects.create(
                    vendor_category=vendor_category_instance,
                    **service_data,
                    added_by_admin=True,
                    approved=True,
                )

            else:
                return Response({"error": "Category doesn't exist!"})

            return Response({"status": "Successfully created service"})


# Assign Agent
class AssignAgentAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, format=None, *args, **kwargs):
        is_assigned = False if request.GET.get("assigned") == "true" else True

        # Get rfq ids with `added_by_admin=true` service value and assigned vendor is null/not null
        rfq_instances = (
            RfqService.objects.filter(
                service__added_by_admin=True,
                rfq_category__rfq__status="approved",
                service__vendor_category__vendor__isnull=is_assigned,
            )
            .values("rfq_category__rfq_id")
            .distinct()
        )

        response_array = []
        for rfq_instance in rfq_instances:
            data = {}

            rfq = Rfq.objects.get(id=rfq_instance["rfq_category__rfq_id"])
            rfq_service_instance = RfqService.objects.filter(
                rfq_category__rfq_id=rfq_instance["rfq_category__rfq_id"],
                service__added_by_admin=True,
                service__vendor_category__vendor__isnull=is_assigned,
            )

            data["rfq"] = BasicRfqSerializer(rfq).data
            data["rfq_services"] = RfqServiceSerializer(
                rfq_service_instance, many=True
            ).data

            response_array.append(data)

        return Response(response_array)

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = AssignServiceSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            # get rfq & vendor service with verification filter
            rfq_service_instance = RfqService.objects.get(
                id=serialized_data.data.get("rfq_service_id"),
                service__added_by_admin=True,
                rfq_category__rfq__status="approved",
            )

            vendor_instance = Vendor.objects.get(
                id=serialized_data.data.get("vendor_id"),
                approved=True,
            )

            # check for category repeatation, if exists then copy the model, attach and update
            # if not, then create category, then copy, attach, update
            # vendor_category = rfq_service_instance.service.vendor_category
            category_id = rfq_service_instance.service.vendor_category.category.id

            # Search Category
            vendor_category_instance = VendorCategory.objects.filter(
                vendor=vendor_instance, category_id=category_id
            )


            if vendor_category_instance.exists():
                # Check if the service already exists
                # if does then only update
                service_instance = Service.objects.filter(
                    vendor_category__vendor=vendor_instance,
                    tracking_id=rfq_service_instance.service.tracking_id,
                )

                if service_instance.exists():
                    # shift
                    rfq_service_instance.service = service_instance.first()
                    rfq_service_instance.save()

                    return Response(
                        {"status": "Successfully assigned service to vendor"}
                    )

                vendor_category_instance = vendor_category_instance.first()

            else:
                vendor_category_instance = VendorCategory.objects.create(
                    vendor=vendor_instance, category_id=category_id
                )

            with transaction.atomic():
                copied_service_instance = rfq_service_instance.service

                # dettach rfq from service
                rfq_service_instance.service = None
                rfq_service_instance.save()

                # copy the service
                copied_service_instance.pk = None
                copied_service_instance.save()

                # attach to vendor
                print(copied_service_instance.pk)
                copied_service_instance.vendor_category = vendor_category_instance
                copied_service_instance.save()

                # assign
                rfq_service_instance.service = copied_service_instance
                rfq_service_instance.save()

            return Response({"status": "Successfully assigned service to vendor"})


# request bill
class UpdateOrderAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, format=None, *args, **kwargs):
        services_instances = RfqService.objects.filter(
            order_status="complete_admin",
        ).order_by("-completed_on")

        serialized_data = BillServicesSerializer(services_instances, many=True)
        return Response(serialized_data.data)

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = AdminDispatchBillSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            RfqService.objects.get(
                id=serialized_data.data.get("id", None), order_status="complete_admin"
            )
