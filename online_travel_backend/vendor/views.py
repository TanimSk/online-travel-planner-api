from dj_rest_auth.registration.views import RegisterView
from .serializers import VendorCustomRegistrationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .serializers import ManageServicesSerializer, RfqServiceSerializer, RfqSerializer
from .models import Service, VendorCategory, Vendor
from agent.models import RfqService, Rfq
from commons.models import Category


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
            )
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


# Managing Tasks
class NewTasksAPI(APIView):
    permission_classes = [AuthenticateOnlyVendor]

    def get(self, request, rfq_id=None, format=None, *args, **kwargs):
        rfq_instances = Rfq.objects.filter(
            rfqcategory_rfq__rfqservice_rfqcategory__service__vendor_category__vendor__vendor=request.user,
            status="assigned",
        ).distinct()

        # rfq_service_instances = RfqService.objects.filter(
        #     service__vendor_category__vendor__vendor=request.user,
        #     rfq_category__rfq__status="assigned",
        # )

        # rfq_services = rfq_service_instances.values("rfq_category__rfq", "id").annotate(
        #     count=Count("rfq_category__rfq"),
        # )

        response_arr = []

        for rfq_instance in rfq_instances:
            obj_data = {}
            obj_data["rfq_details"] = RfqSerializer(rfq_instance).data

            services_instance = RfqService.objects.filter(
                rfq_category__rfq=rfq_instance
            )
            # print(services_instance)
            serialized_data = RfqServiceSerializer(services_instance, many=True)
            obj_data["services_details"] = serialized_data.data

            response_arr.append(obj_data)

        # serialized_service = RfqServiceSerializer(rfq_services, many=True)
        # print(response_arr)

        return Response(response_arr)
