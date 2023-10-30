from dj_rest_auth.registration.views import RegisterView
from .serializers import VendorCustomRegistrationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404

from .serializers import ManageServicesSerializer
from .models import Service, VendorCategory, Vendor
from administrator.models import Category


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
