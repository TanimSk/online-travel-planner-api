from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import Agent, Rfq, RfqCategory, RfqService
from vendor.models import Service
from django.db import transaction
from commons.models import Bill
from django.db.models import Sum
from datetime import datetime


class AgentCustomRegistrationSerializer(RegisterSerializer):
    agent = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )  # by default allow_null = False
    agent_name = serializers.CharField(required=True)
    agency_name = serializers.CharField(required=True)
    agent_address = serializers.CharField(required=True)
    mobile_no = serializers.CharField(required=True)
    logo_url = serializers.URLField(required=True)
    trade_license_url = serializers.URLField(required=True)

    def get_cleaned_data(self):
        data = super(AgentCustomRegistrationSerializer, self).get_cleaned_data()
        extra_data = {
            "agent_name": self.validated_data.get("agent_name", ""),
            "agency_name": self.validated_data.get("agency_name", ""),
            "agent_address": self.validated_data.get("agent_address", ""),
            "mobile_no": self.validated_data.get("mobile_no", ""),
            "logo_url": self.validated_data.get("logo_url", ""),
            "trade_license_url": self.validated_data.get("trade_license_url", ""),
        }
        data.update(extra_data)
        return data

    def save(self, request):
        user = super(AgentCustomRegistrationSerializer, self).save(request)
        user.is_agent = True
        user.save()
        agent = Agent(
            agent=user,
            agent_name=self.cleaned_data.get("agent_name"),
            agency_name=self.cleaned_data.get("agency_name"),
            agent_address=self.cleaned_data.get("agent_address"),
            mobile_no=self.cleaned_data.get("mobile_no"),
            logo_url=self.cleaned_data.get("logo_url"),
            trade_license_url=self.cleaned_data.get("trade_license_url"),
        )
        agent.save()
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


class RfqSerializer(serializers.ModelSerializer):
    rfq_categories = RfqCategorySerializer(many=True)
    total_price = serializers.SerializerMethodField(method_name="get_total_price")

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

        # get days difference
        if (rfq_service_instance.get("check_in_date", None) is None) and (
            rfq_service_instance.get("check_out_date", None) is None
        ):
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
            date1 = datetime.strptime(
                rfq_service_instance.get("check_in_date", None), date_format
            )
            date2 = datetime.strptime(
                rfq_service_instance.get("check_out_date", None), date_format
            )
            delta_days = abs((date2 - date1).days)

        total_price = (
            (
                service_instance.infant_price
                * rfq_service_instance.get("infant_members", 0)
            )
            + (
                service_instance.child_price
                * rfq_service_instance.get("child_members", 0)
            )
            + (
                service_instance.adult_price
                * rfq_service_instance.get("adult_members", 0)
            )
            + (service_instance.service_price * rfq_service_instance.get("members", 0))
            * delta_days
            + (service_instance.cost_per_hour) * rfq_service_instance.get("duration", 0)
        )

        agent_commission = Agent.objects.get(
            agent=self.context.get("request").user
        ).commission

        # appending commissions
        total_price = (
            total_price
            + (total_price * service_instance.admin_commission * 0.01)
            + (total_price * agent_commission * 0.01)
        )

        return total_price

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
                )
        return {"total_price": total_price, "total_services": total_services}

    def create(self, validated_data):
        rfq_total_price = 0

        with transaction.atomic():
            rfq_categories = validated_data.pop("rfq_categories")
            validated_data.pop("total_price")

            rfq_instance = Rfq.objects.create(
                agent=self.context.get("request").user, **validated_data
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
                    total_price = self.calc_total_price_value(
                        service_instance, rfq_service
                    )
                    rfq_total_price += total_price

                    agent_commission = Agent.objects.get(
                        agent=self.context.get("request").user
                    ).commission

                    RfqService.objects.create(
                        rfq_category=rfq_category_instance,
                        service=service_instance,
                        service_price=total_price,
                        **rfq_service,
                        admin_commission=service_instance.admin_commission,
                        agent_commission=agent_commission
                    )

            rfq_instance.total_price = rfq_total_price
            rfq_instance.save()

        return rfq_instance


# Query
class QueryServiceSerializer(serializers.Serializer):
    # pop keys with empty value
    def to_internal_value(self, data):
        copy_data = data.copy()
        for dat in data:
            if data[dat] == "":
                copy_data.pop(dat)

        return super(QueryServiceSerializer, self).to_internal_value(copy_data)

    category_id = serializers.IntegerField(required=True)

    # venue sourcing
    area_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # hotel booking
    # hotel_name = serializers.CharField(
    #     required=False, allow_null=True, allow_blank=True
    # )
    room_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    bed_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # members
    infant_members = serializers.IntegerField(required=False, allow_null=True)
    child_members = serializers.IntegerField(required=False, allow_null=True)
    adult_members = serializers.IntegerField(required=False, allow_null=True)
    members = serializers.IntegerField(required=False, allow_null=True)

    # flight booking + transportation
    from_area = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    to_area = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # flight booking
    flight_class = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    trip_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    depart_time = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )
    return_time = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    # entertainment - v
    # meeting and event management - v
    # special activities

    # event decoration
    event_type = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    event_venue = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    # sight seeing
    day_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    transfer_type = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    # daily transportation
    car_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class QueryResultSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField(method_name="get_total_price")
    category_name = serializers.CharField(
        source="vendor_category.category.category_name", read_only=True
    )
    category_id = serializers.IntegerField(source="vendor_category.category.id")

    def get_total_price(self, instance):
        dictionary = self.context["dictionary"]
        copied_dict = dictionary.copy()

        # Remove empty values
        for dat in dictionary:
            if dictionary[dat] == None:
                copied_dict.pop(dat)

        total_price = (
            (instance.infant_price * copied_dict.get("infant_members", 0))
            + (instance.child_price * copied_dict.get("child_members", 0))
            + (instance.adult_price * copied_dict.get("adult_members", 0))
            + (instance.service_price * copied_dict.get("members", 0))
        )
        return total_price

    class Meta:
        exclude = (
            "vendor_category",
            "approved",
            "added_by_admin",
        )
        model = Service


# Bill request serializer
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
            "agent_billed_on",
            "agent_bill",
            "agent_due",
            "total_bill",
            "customer_name",
            "customer_address",
            "contact_no",
            "service_name",
        )

    def get_total_bill(self, obj):
        return obj.vendor_bill + obj.admin_bill + obj.agent_bill


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
            "admin_paid_on",
            "agent_bill",
            "total_bill",
            "customer_name",
            "customer_address",
            "contact_no",
            "service_name",
            "paid_amount",
        )

    def get_total_bill(self, obj):
        return obj.vendor_bill + obj.admin_bill + obj.agent_bill

    def get_paid_amount(self, obj):
        return obj.vendor_bill + obj.admin_bill + obj.agent_bill - obj.agent_due


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


class CommissionSerializer(serializers.Serializer):
    commission = serializers.FloatField(required=True)


class ServiceInfo(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="vendor_category.category.category_name"
    )
    category_description = serializers.CharField(
        source="vendor_category.category.description"
    )

    class Meta:
        fields = (
            "id",
            "service_name",
            "image_urls",
            "description",
            "category_name",
            "category_description",
            "overview",
            "itinerary",
            "rates",
        )
        model = Service


class SuggestionSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    field_content = serializers.CharField(allow_blank=True)
    category_id = serializers.IntegerField()
