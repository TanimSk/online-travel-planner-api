from dj_rest_auth.registration.views import RegisterView
from .serializers import VendorCustomRegistrationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .serializers import (
    ManageServicesSerializer,
    RfqServiceSerializer,
    BillServicesSerializer,
    DispatchBillServiceSerializer,
    RfqServiceUpdateSerializer,
)
from administrator.serializers import BasicRfqSerializer
from .models import Service, VendorCategory, Vendor
from agent.models import RfqService, Rfq
from commons.models import Category, Bill


# Authenticate Vendor Only Class
class AuthenticateOnlyVendor(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_vendor:
                return True
            else:
                return False
        return False


class VendorRegistrationView(RegisterView):
    serializer_class = VendorCustomRegistrationSerializer


class ManageServicesAPI(APIView):
    serializer_class = ManageServicesSerializer
    permission_classes = [AuthenticateOnlyVendor]

    def get(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            instance = Service.objects.filter(
                vendor_category__vendor__vendor=request.user
            ).order_by("-created_on")
            serialized_data = self.serializer_class(instance, many=True)
            return Response(serialized_data.data)

        try:
            instance = Service.objects.get(
                id=service_id, vendor_category__vendor__vendor=request.user
            )
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

            # Create category, if not exists
            try:
                vendor_category_instance = VendorCategory.objects.get(
                    vendor__vendor=request.user, category_id=category_id
                )
                Service.objects.create(
                    vendor_category=vendor_category_instance, **service_data
                )

            except VendorCategory.DoesNotExist:
                vendor_instance = get_object_or_404(Vendor, vendor=request.user)

                # Check if Category exists
                if Category.objects.filter(id=category_id).exists():
                    vendor_category_instance = VendorCategory.objects.create(
                        category_id=category_id, vendor=vendor_instance
                    )
                    Service.objects.create(
                        vendor_category=vendor_category_instance, **service_data
                    )

                else:
                    return Response({"error": "Category doesn't exist!"})

            return Response({"status": "Successfully created service"})

    def put(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            return Response({"error": "Service id missing"})

        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            service_data = serialized_data.data
            service_data.pop("category_id")
            category_id = serialized_data.data.get("category_id")

            # Create category, if not exists
            try:
                vendor_category_instance = VendorCategory.objects.get(
                    vendor__vendor=request.user, category_id=category_id
                )
                service_instance = Service.objects.filter(
                    vendor_category=vendor_category_instance, id=service_id
                )
                service_instance.update(**service_data)

                return Response({"status": "Successfully updated service"})

            except VendorCategory.DoesNotExist:
                return Response({"error": "Category doesn't exist!"})


# Managing Tasks
class NewTasksAPI(APIView):
    permission_classes = [AuthenticateOnlyVendor]

    def get(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            # Get only completed tasks
            if request.GET.get("completed", None) == "true":
                rfq_instances = (
                    RfqService.objects.filter(
                        # service__added_by_admin=True,
                        service__vendor_category__vendor__vendor=request.user,
                        # rfq_category__rfq__status="completed",
                        service__vendor_category__vendor__isnull=False,
                        order_status="dispatched",
                    )
                    .order_by("-id")
                    .values("rfq_category__rfq_id")
                    .distinct()
                )
            else:
                # Get incompleted tasks
                rfq_instances = (
                    RfqService.objects.filter(
                        # service__added_by_admin=True,
                        service__vendor_category__vendor__vendor=request.user,
                        rfq_category__rfq__status="confirmed",
                        service__vendor_category__vendor__isnull=False,
                    )
                    .exclude(order_status="dispatched")
                    # .exclude(order_status="complete")
                    .order_by("-id")
                    .values("rfq_category__rfq_id")
                    .distinct()
                )

            response_array = []
            for rfq_instance in rfq_instances:
                data = {}

                rfq = Rfq.objects.get(id=rfq_instance["rfq_category__rfq_id"])

                if request.GET.get("completed", None) == "true":
                    # Get only completed tasks
                    rfq_service_instance = RfqService.objects.filter(
                        rfq_category__rfq_id=rfq_instance["rfq_category__rfq_id"],
                        # service__added_by_admin=True,
                        service__vendor_category__vendor__isnull=False,
                        order_status="dispatched",
                    ).order_by("-id")
                else:
                    # Get only completed tasks
                    rfq_service_instance = (
                        RfqService.objects.filter(
                            rfq_category__rfq_id=rfq_instance["rfq_category__rfq_id"],
                            # service__added_by_admin=True,
                            service__vendor_category__vendor__isnull=False,
                        )
                        # .exclude(order_status="complete")
                        .exclude(order_status="dispatched").order_by("-id")
                    )

                data["rfq"] = BasicRfqSerializer(rfq).data
                data["rfq_services"] = RfqServiceSerializer(
                    rfq_service_instance, many=True
                ).data

                response_array.append(data)

            return Response(response_array)

        else:
            data = {}
            rfq = (
                Rfq.objects.filter(
                    rfqcategory_rfq__rfqservice_rfqcategory__service__vendor_category__vendor__vendor=request.user,
                )
                .distinct()
                .get(id=rfq_id)
            )

            # Filtering
            if request.GET.get("completed", None) == "true":
                # completed tasks
                rfq_service_instance = RfqService.objects.filter(
                    rfq_category__rfq=rfq, order_status="dispatched"
                ).order_by("-id")
            else:
                rfq_service_instance = (
                    RfqService.objects.filter(
                        rfq_category__rfq=rfq,
                    )
                    # .exclude(order_status="complete")
                    .exclude(order_status="dispatched").order_by("-id")
                )

            data["rfq"] = BasicRfqSerializer(rfq).data
            data["rfq_services"] = RfqServiceSerializer(
                rfq_service_instance, many=True
            ).data

            return Response(data)

    def put(self, request, rfq_id=None, format=None, *args, **kwargs):
        serialized_data = RfqServiceUpdateSerializer(data=request.data, many=True)

        if serialized_data.is_valid(raise_exception=True):
            rfq_instance = (
                Rfq.objects.filter(
                    rfqcategory_rfq__rfqservice_rfqcategory__service__vendor_category__vendor__vendor=request.user,
                    status="confirmed",
                )
                .filter(id=rfq_id)
                .first()
            )

            # Update service one by one
            for service in serialized_data.data:
                rfq_service_instance = RfqService.objects.get(
                    id=service.get("service_id"), rfq_category__rfq=rfq_instance
                )

                # print(rfq_service_instance.order_status)
                rfq_service_instance.order_status = service.get("order_status")

                # Set completed on date & make bill, if completed
                if service.get("order_status") == "dispatched":
                    rfq_service_instance.completed_on = timezone.now()

                    # # Calculate & Make Bill
                    # Bill.objects.create(
                    #     vendor=request.user,
                    #     agent=rfq_service_instance.rfq_category.rfq.agent,
                    #     tracking_id=rfq_service_instance.tracing_id,
                    #     vendor_bill=rfq_service_instance.service_price,
                    #     admin_bill=rfq_service_instance.service_price
                    #     * rfq_service_instance.admin_commission
                    #     * 0.01,
                    #     agent_bill=rfq_service_instance.service_price
                    #     * rfq_service_instance.agent_commission
                    #     * 0.01,
                    # )

                rfq_service_instance.save()

            return Response({"status": "Successfully updated services"})


class RequestBillAPI(APIView):
    permission_classes = [AuthenticateOnlyVendor]

    def get(self, request, format=None, *args, **kwargs):
        bills_instance = Bill.objects.filter(
            vendor=request.user, status_2="vendor_bill"
        ).order_by("-created_on")
        serialized_data = BillServicesSerializer(bills_instance, many=True)
        return Response(serialized_data.data)

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = DispatchBillServiceSerializer(data=request.data, many=True)

        if serialized_data.is_valid(raise_exception=True):
            for service in serialized_data.data:
                bill_instance = Bill.objects.get(
                    tracking_id=service.get("tracking_id"),
                )
                bill_instance.status_2 = "admin_bill"
                bill_instance.admin_billed_on = timezone.now()
                bill_instance.save()

            return Response({"status": "Successfully requested for bill to admin"})


class PayBillAPI(APIView):
    permission_classes = [AuthenticateOnlyVendor]

    def get(self, request, format=None, *args, **kwargs):
        bills_instance = Bill.objects.filter(
            vendor=request.user, status_2="vendor_paid"
        ).order_by("-vendor_paid_on")
        serialized_data = BillServicesSerializer(bills_instance, many=True)
        return Response(serialized_data.data)
