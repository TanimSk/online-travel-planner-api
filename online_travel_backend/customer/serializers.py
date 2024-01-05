from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer

from agent.models import Rfq, RfqCategory, RfqService
from vendor.models import Service
from .models import Customer

from django.db.models import Sum
from django.db import transaction


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


class RfqServiceSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("rfq_category",)
        model = RfqService


class RfqCategorySerializer(serializers.ModelSerializer):
    rfq_services = RfqServiceSerializer(many=True)

    class Meta:
        exclude = ("rfq",)
        model = RfqCategory


# RFQ
class RfqSerializer(serializers.ModelSerializer):
    rfq_categories = RfqCategorySerializer(many=True)
    total_price = serializers.SerializerMethodField(method_name="get_total_price")

    customer_name = serializers.CharField(required=False)
    customer_address = serializers.CharField(required=False)
    contact_no = serializers.CharField(required=False)
    email_address = serializers.EmailField(required=False)

    class Meta:
        exclude = ("agent",)
        model = Rfq

    def get_total_price(self, instance):
        if not self.context.get("total_price", True):
            return None

        return RfqService.objects.filter(rfq_category__rfq=instance).aggregate(
            price=Sum("service_price")
        )["price"]

    # pop keys with empty value
    def to_internal_value(self, data):
        copy_data = data.copy()

        for dat_index, dat in enumerate(data["rfq_categories"]):
            for ser_index, service in enumerate(dat["rfq_services"]):
                keys_to_remove = []
                for datapoint in service:
                    if service[datapoint] == "":
                        keys_to_remove.append(datapoint)

                for key in keys_to_remove:
                    copy_data["rfq_categories"][dat_index]["rfq_services"][
                        ser_index
                    ].pop(key)

        return super(RfqSerializer, self).to_internal_value(copy_data)

    def calc_total_price(self, validated_data):
        rfq_categories = validated_data.pop("rfq_categories")

        total_price = 0
        total_services = 0

        for rfq_category in rfq_categories:
            rfq_services = rfq_category.pop("rfq_services")

            for rfq_service in rfq_services:
                service_id = rfq_service.pop("service")

                try:
                    rfq_service.pop("service_price")
                except KeyError:
                    pass

                # price calculation
                service_instance = Service.objects.get(id=service_id)
                total_services += 1
                total_price += (
                    (
                        service_instance.infant_price
                        * rfq_service.get("infant_members", 0)
                    )
                    + (
                        service_instance.child_price
                        * rfq_service.get("child_members", 0)
                    )
                    + (
                        service_instance.adult_price
                        * rfq_service.get("adult_members", 0)
                    )
                    + (service_instance.service_price * rfq_service.get("members", 0))
                )

        return {"total_price": total_price, "total_services": total_services}

    def create(self, validated_data):
        rfq_total_price = 0

        with transaction.atomic():
            rfq_categories = validated_data.pop("rfq_categories")

            # pop unnecessary data for creating rfq
            validated_data.pop("total_price")
            # validated_data.pop("customer_name")
            # validated_data.pop("customer_address")
            # validated_data.pop("email_address")
            # validated_data.pop("contact_no")

            rfq_instance = Rfq.objects.create(
                customer=self.context.get("request").user,
                customer_name=self.context.get("request").user.customer.customer_name,
                customer_address=self.context.get(
                    "request"
                ).user.customer.customer_address,
                email_address=self.context.get("request").user.email,
                contact_no=self.context.get("request").user.customer.customer_number,
                **validated_data,
            )

            for rfq_category in rfq_categories:
                rfq_services = rfq_category.pop("rfq_services")
                rfq_category_instance = RfqCategory.objects.create(
                    rfq=rfq_instance, category_id=rfq_category.get("category")
                )

                for rfq_service in rfq_services:
                    service_id = rfq_service.pop("service")

                    try:
                        rfq_service.pop("service_price")
                    except KeyError:
                        pass

                    # price calculation
                    service_instance = Service.objects.get(id=service_id)
                    total_price = (
                        (
                            service_instance.infant_price
                            * rfq_service.get("infant_members", 0)
                        )
                        + (
                            service_instance.child_price
                            * rfq_service.get("child_members", 0)
                        )
                        + (
                            service_instance.adult_price
                            * rfq_service.get("adult_members", 0)
                        )
                        + (
                            service_instance.service_price
                            * rfq_service.get("members", 0)
                        )
                    )

                    rfq_total_price += total_price + (
                        total_price * service_instance.admin_commission * 0.01
                    )

                    RfqService.objects.create(
                        rfq_category=rfq_category_instance,
                        service=service_instance,
                        service_price=total_price,
                        **rfq_service,
                        admin_commission=service_instance.admin_commission,
                    )

            rfq_instance.total_price = rfq_total_price
            rfq_instance.save()

        return rfq_instance
