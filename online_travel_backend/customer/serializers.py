from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import Customer


class CustomerCustomRegistrationSerializer(RegisterSerializer):
    vendor = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )  # by default allow_null = False
    customer_name = serializers.CharField(required=True)
    customer_address = serializers.CharField(required=True)
    customer_number = serializers.CharField(required=True)

    def get_cleaned_data(self):
        data = super(CustomerCustomRegistrationSerializer, self).get_cleaned_data()
        extra_data = {
            "customer_name": self.validated_data.get("customer_name", ""),
            "customer_address": self.validated_data.get("customer_address", ""),
            "customer_number": self.validated_data.get("customer_number", ""),
        }
        data.update(extra_data)
        return data

    def save(self, request):
        user = super(CustomerCustomRegistrationSerializer, self).save(request)
        user.is_customer = True
        user.save()
        vendor = Customer(
            customer=user,
            customer_name=self.cleaned_data.get("customer_name", ""),
            customer_address=self.cleaned_data.get("customer_address"),
            customer_number=self.cleaned_data.get("customer_number"),            
        )
        vendor.save()
        return user
