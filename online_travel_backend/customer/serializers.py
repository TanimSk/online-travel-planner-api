from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer

from agent.models import Rfq, RfqCategory, RfqService
from vendor.models import Service
from .models import Customer

from django.db.models import Sum
from django.db import transaction
from datetime import datetime


class CustomerCustomRegistrationSerializer(RegisterSerializer):
    vendor = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )  # by default allow_null = False
    customer_name = serializers.CharField(required=True)
    customer_address = serializers.CharField(required=True)
    customer_number = serializers.CharField(required=True)
    customer_nationality = serializers.CharField(required=True)
    customer_country_code = serializers.CharField(required=True)

    def get_cleaned_data(self):
        data = super(CustomerCustomRegistrationSerializer, self).get_cleaned_data()
        extra_data = {
            "customer_name": self.validated_data.get("customer_name", ""),
            "customer_address": self.validated_data.get("customer_address", ""),
            "customer_number": self.validated_data.get("customer_number", ""),
            "customer_nationality": self.validated_data.get("customer_nationality", ""),
            "customer_country_code": self.validated_data.get(
                "customer_country_code", ""
            ),
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
            customer_nationality=self.cleaned_data.get("customer_nationality"),
            customer_country_code=self.cleaned_data.get("customer_country_code"),
        )
        vendor.save()
        return user


class RfqServiceSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("rfq_category", "base_price")
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
    _members = serializers.IntegerField(required=False)

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

    # get total price
    def calc_total_price_value(self, service_instance, rfq_service_instance):
        delta_days = 1

        # get days diff
        if not (
            (rfq_service_instance.get("check_in_date", None) is None)
            and (rfq_service_instance.get("check_out_date", None) is None)
        ):
            # print(rfq_service_instance.get("check_in_date", None))
            date_format = "%Y-%m-%dT%H:%M:%S%z"
            date1 = datetime.strptime(
                rfq_service_instance.get("check_in_date", None), date_format
            )
            date2 = datetime.strptime(
                rfq_service_instance.get("check_out_date", None), date_format
            )
            delta_days = abs((date2 - date1).days) + 1

        # calculate with duration, car quantity, quantity
        added_price = 0

        if rfq_service_instance.get("duration"):
            added_price = service_instance.service_price * rfq_service_instance.get(
                "duration", 0
            )
            if rfq_service_instance.get("car_quantity"):
                added_price = added_price * rfq_service_instance.get("car_quantity", 0)

        if rfq_service_instance.get("quantity"):
            added_price += (service_instance.service_price) * rfq_service_instance.get(
                "quantity", 0
            )

        total_price = (
            (
                # hotel booking
                (
                    service_instance.service_price
                    * rfq_service_instance.get("total_room", 0)
                    * delta_days
                )
                + (
                    service_instance.extra_breakfast_price
                    * int(rfq_service_instance.get("include_breakfast", 0))
                    * (
                        rfq_service_instance.get("child_members", 0)
                        + rfq_service_instance.get("adult_members", 0)
                    )
                )
                + (
                    service_instance.extra_bed_price
                    * rfq_service_instance.get("total_extra_bed", 0)
                )
            )
            # others
            + (
                (
                    service_instance.service_price
                    * rfq_service_instance.get("members", 0)
                )
            )
            + added_price
        )

        # appending commissions
        total_price_added = total_price + (
            total_price * service_instance.admin_commission * 0.01
        )

        return [total_price_added, total_price]

    # get json
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
                total_price += self.calc_total_price_value(
                    service_instance, rfq_service
                )[0]
        return {"total_price": total_price, "total_services": total_services}

    def create(self, validated_data):
        rfq_total_price = 0

        with transaction.atomic():
            rfq_categories = validated_data.pop("rfq_categories")

            # pop unnecessary data for creating rfq
            # validated_data.pop("total_price")
            # validated_data.pop("customer_name")
            # validated_data.pop("customer_address")
            # validated_data.pop("email_address")
            # validated_data.pop("contact_no")

            customer_instance = Customer.objects.get(
                customer=self.context.get("request").user
            )

            # print(validated_data)

            # setting customer data to itself
            rfq_instance = Rfq.objects.create(
                agent=self.context.get("agent").agent,
                customer=self.context.get("request").user,
                customer_name=customer_instance.customer_name,
                customer_address=customer_instance.customer_address,
                email_address=self.context.get("request").user.email,
                contact_no=customer_instance.customer_number,
                travel_date=validated_data.get("travel_date"),
            )

            for rfq_category in rfq_categories:
                rfq_services = rfq_category.pop("rfq_services")
                rfq_category_instance = RfqCategory.objects.create(
                    rfq=rfq_instance, category_id=rfq_category.get("category")
                )

                for rfq_service in rfq_services:
                    service_id = rfq_service.pop("service")
                    total_members = rfq_service.get("members", 0) + rfq_service.get(
                        "_members", 0
                    )

                    # price calculation
                    service_instance = Service.objects.get(id=service_id)

                    total_price = self.calc_total_price_value(
                        service_instance, rfq_service
                    )

                    for key in [
                        "service_price",
                        "room_type",
                        "bed_type",
                        "services_name",
                        "area_name",
                        "members",
                        "_members",
                    ]:
                        try:
                            rfq_service.pop(key)
                        except KeyError:
                            pass

                    # price with commission
                    rfq_total_price += total_price[0]

                    RfqService.objects.create(
                        rfq_category=rfq_category_instance,
                        service=service_instance,
                        ########
                        service_price=total_price[0],
                        base_price=total_price[1],
                        ######
                        room_type=service_instance.room_type,
                        bed_type=service_instance.bed_type,
                        services_name=service_instance.services_name,
                        area_name=service_instance.area_name,
                        ######
                        members=total_members,
                        **rfq_service,
                        admin_commission=service_instance.admin_commission,
                    )

            rfq_instance.total_price = rfq_total_price
            rfq_instance.save()

        return rfq_instance


class ProfileSerializer(serializers.ModelSerializer):
    email_address = serializers.EmailField(source="customer.email", read_only=True)

    class Meta:
        model = Customer
        exclude = (
            "customer",
            "added_on",
            "confirmed",
        )


class ServiceInfo(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="vendor_category.category.category_name"
    )
    category_description = serializers.CharField(
        source="vendor_category.category.description"
    )
    category_id = serializers.IntegerField(source="vendor_category.category.id")

    class Meta:
        fields = (
            "id",
            "category_id",
            "service_name",
            "image_urls",
            "description",
            "category_name",
            "category_description",
            "overview",
            "itinerary",
            "rates",
            "services_name",
            "cover_img",
        )
        model = Service
