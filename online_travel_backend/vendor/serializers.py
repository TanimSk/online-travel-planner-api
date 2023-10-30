from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import Vendor, Service


class VendorCustomRegistrationSerializer(RegisterSerializer):
    vendor = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )  # by default allow_null = False
    contact_name = serializers.CharField(required=True)
    vendor_name = serializers.CharField(required=True)
    vendor_address = serializers.CharField(required=True)
    vendor_number = serializers.CharField(required=True)
    logo_url = serializers.URLField(required=True)

    def get_cleaned_data(self):
        data = super(VendorCustomRegistrationSerializer, self).get_cleaned_data()
        extra_data = {
            "contact_name": self.validated_data.get("contact_name", ""),
            "vendor_name": self.validated_data.get("vendor_name", ""),
            "vendor_address": self.validated_data.get("vendor_address", ""),
            "vendor_number": self.validated_data.get("vendor_number", ""),
            "logo_url": self.validated_data.get("vendor_number", "logo_url"),
        }
        data.update(extra_data)
        return data

    def save(self, request):
        user = super(VendorCustomRegistrationSerializer, self).save(request)
        user.is_vendor = True
        user.save()
        vendor = Vendor(
            vendor=user,
            contact_name=self.cleaned_data.get("contact_name"),
            vendor_name=self.cleaned_data.get("vendor_name"),
            vendor_address=self.cleaned_data.get("vendor_address"),
            vendor_number=self.cleaned_data.get("vendor_number"),
            logo_url=self.cleaned_data.get("logo_url"),
        )
        vendor.save()
        return user


# Manage Services
class ManageServicesSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="vendor_category.category.category_name", read_only=True
    )

    category_id = serializers.IntegerField(source="vendor_category.category.id")

    class Meta:
        exclude = ("vendor_category",)
        model = Service
