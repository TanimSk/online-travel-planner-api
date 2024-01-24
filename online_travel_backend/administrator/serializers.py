from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import Administrator
from agent.models import Rfq, RfqCategory, RfqService, Agent

# from django.conf import settings
from commons.models import Bill
from vendor.models import Vendor, VendorCategory, Service
from customer.models import Customer


class AdminCustomRegistrationSerializer(RegisterSerializer):
    administrator = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )  # by default allow_null = False
    admin_name = serializers.CharField(required=True)
    mobile_no = serializers.CharField(required=True)

    def get_cleaned_data(self):
        data = super(AdminCustomRegistrationSerializer, self).get_cleaned_data()
        extra_data = {
            "admin_name": self.validated_data.get("admin_name", ""),
            "mobile_no": self.validated_data.get("mobile_no", ""),
            "password_txt": self.validated_data.get("password1", ""),
        }
        data.update(extra_data)
        return data

    def save(self, request):
        user = super(AdminCustomRegistrationSerializer, self).save(request)
        user.is_admin = True
        user.save()
        administrator = Administrator(
            administrator=user,
            admin_name=self.cleaned_data.get("admin_name"),
            mobile_no=self.cleaned_data.get("mobile_no"),
            password_txt=self.cleaned_data.get("password_txt"),
        )
        administrator.save()
        return user


class AgentSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="agent.email")

    class Meta:
        model = Agent
        exclude = ("agent",)


class CustomerSerializer(serializers.ModelSerializer):
    email_address = serializers.EmailField(source="customer.email", read_only=True)

    class Meta:
        model = Customer
        exclude = (
            "customer",
            "confirmed",
        )


# RFQ
class RfqServiceSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("rfq_category",)
        model = RfqService
        depth = 1


class RfqCategorySerializer(serializers.ModelSerializer):
    rfq_services = RfqServiceSerializer(many=True)

    class Meta:
        exclude = ("rfq",)
        model = RfqCategory
        depth = 1


class RfqSerializer(serializers.ModelSerializer):
    rfq_categories = RfqCategorySerializer(many=True)
    agent_info = AgentSerializer(read_only=True)

    class Meta:
        exclude = (
            "agent",
            "approved_on",
        )
        model = Rfq


class ApprovalSerializer(serializers.Serializer):
    approved = serializers.BooleanField(required=True)


# Vendor
class VendorServiceSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("service_name",)
        model = Service


class VendorCategorySerializer(serializers.ModelSerializer):
    vendor_services = VendorServiceSerializer(many=True)
    category_name = serializers.CharField(source="category.category_name")

    class Meta:
        fields = (
            "category_name",
            "vendor_services",
        )
        model = VendorCategory


class VendorListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="vendor.email")
    vendor_categories = VendorCategorySerializer(many=True)

    class Meta:
        exclude = ("approved",)
        model = Vendor


class EditPriceSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    service_price = serializers.FloatField()
    remarks = serializers.CharField()


# assign vendor
class BasicRfqSerializer(serializers.ModelSerializer):
    agent_info = AgentSerializer(read_only=True)

    class Meta:
        exclude = (
            "agent",
            "approved_on",
        )
        model = Rfq


# Update commission in services
class UpdateCommissionSerializer(serializers.Serializer):
    commission = serializers.FloatField(required=True)


class AssignServiceSerializer(serializers.Serializer):
    rfq_service_id = serializers.IntegerField(required=True)
    vendor_id = serializers.IntegerField(required=True)


# Received Payments
class ReceivedPaymentSerializer(serializers.ModelSerializer):
    total_bill = serializers.SerializerMethodField()
    received_money = serializers.SerializerMethodField()

    customer_name = serializers.CharField(
        source="service.rfq_category.rfq.customer_name"
    )
    customer_address = serializers.CharField(
        source="service.rfq_category.rfq.customer_address"
    )
    contact_no = serializers.CharField(source="service.rfq_category.rfq.contact_no")
    service_name = serializers.CharField(source="service.service.service_name")

    class Meta:
        model = Bill
        fields = (
            "tracking_id",
            "vendor_bill",
            "admin_bill",
            "total_bill",
            "customer_name",
            "customer_address",
            "contact_no",
            "service_name",
            "received_money",
        )

    def get_total_bill(self, obj):
        return obj.vendor_bill + obj.admin_bill

    def get_received_money(self, obj):
        return obj.vendor_bill + obj.admin_bill - obj.agent_due


# Bill Request
class BillServicesSerializer(serializers.ModelSerializer):
    total_bill = serializers.SerializerMethodField()

    customer_name = serializers.CharField(
        source="service.rfq_category.rfq.customer_name"
    )
    customer_address = serializers.CharField(
        source="service.rfq_category.rfq.customer_address"
    )
    contact_no = serializers.CharField(source="service.rfq_category.rfq.contact_no")
    service_name = serializers.CharField(source="service.service.service_name")

    class Meta:
        model = Bill
        fields = (
            "tracking_id",
            "vendor_bill",
            "admin_bill",
            "total_bill",
            "customer_name",
            "customer_address",
            "contact_no",
            "service_name",
        )

    def get_total_bill(self, obj):
        return obj.vendor_bill + obj.admin_bill


class BillRequestSerializer(serializers.ModelSerializer):
    total_bill = serializers.SerializerMethodField()
    customer_name = serializers.CharField(
        source="service.rfq_category.rfq.customer_name"
    )
    customer_address = serializers.CharField(
        source="service.rfq_category.rfq.customer_address"
    )
    contact_no = serializers.CharField(source="service.rfq_category.rfq.contact_no")
    service_name = serializers.CharField(source="service.service.service_name")

    class Meta:
        model = Bill
        fields = (
            "tracking_id",
            "admin_billed_on",
            "admin_bill",
            "admin_due",
            "total_bill",
            "customer_name",
            "customer_address",
            "contact_no",
            "service_name",
        )

    def get_total_bill(self, obj):
        return obj.vendor_bill

    # + obj.admin_bill


# Bill Request
class PaidBillSerializer(serializers.ModelSerializer):
    total_bill = serializers.SerializerMethodField()
    customer_name = serializers.CharField(
        source="service.rfq_category.rfq.customer_name"
    )
    customer_address = serializers.CharField(
        source="service.rfq_category.rfq.customer_address"
    )
    contact_no = serializers.CharField(source="service.rfq_category.rfq.contact_no")
    service_name = serializers.CharField(source="service.service.service_name")

    paid_amount = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = (
            "tracking_id",
            "vendor_paid_on",
            "admin_bill",
            "total_bill",
            "customer_name",
            "customer_address",
            "contact_no",
            "service_name",
            "paid_amount",
        )

    def get_total_bill(self, obj):
        return obj.vendor_bill

    # + obj.admin_bill

    def get_paid_amount(self, obj):
        return obj.vendor_bill - obj.admin_due


class BillPaySerializer(serializers.ModelSerializer):
    tracking_id = serializers.UUIDField()
    paid_amount = serializers.FloatField()

    class Meta:
        model = Bill
        fields = (
            "tracking_id",
            "admin_payment_type",
            "paid_amount",
        )


# Vendor Registration Serializer
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
            "password_text": self.validated_data.get("password1", ""),
        }
        data.update(extra_data)
        return data

    def save(self, request):
        user = super(VendorCustomRegistrationSerializer, self).save(request)
        user.is_vendor = True
        user.save()
        vendor = Vendor(
            vendor=user,
            password_text=self.cleaned_data.get("password_text", ""),
            contact_name=self.cleaned_data.get("contact_name"),
            vendor_name=self.cleaned_data.get("vendor_name"),
            vendor_address=self.cleaned_data.get("vendor_address"),
            vendor_number=self.cleaned_data.get("vendor_number"),
            logo_url=self.cleaned_data.get("logo_url"),
            approved=True,
        )
        vendor.save()
        return user
