from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import Agent, Rfq, RfqCategory, RfqService
from vendor.models import Service
from django.db import transaction


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

    class Meta:
        exclude = ("agent",)
        model = Rfq

    def create(self, validated_data):
        with transaction.atomic():
            rfq_categories = validated_data.pop("rfq_categories")
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
                    total_price = (
                        (
                            service_instance.infant_price
                            * rfq_service.get("infant_members")
                        )
                        + (
                            service_instance.child_price
                            * rfq_service.get("child_members")
                        )
                        + (
                            service_instance.adult_price
                            * rfq_service.get("adult_members")
                        )
                        + (service_instance.service_price * rfq_service.get("members"))
                    )

                    RfqService.objects.create(
                        rfq_category=rfq_category_instance,
                        service=service_instance,
                        service_price=total_price,
                        **rfq_service,
                    )

        return rfq_instance


# Query
class QueryServiceSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=True)

    # venue sourcing
    area_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # hotel booking
    hotel_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
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
        total_price = (
            (instance.infant_price * dictionary.get("infant_members", 0))
            + (instance.child_price * dictionary.get("child_members", 0))
            + (instance.adult_price * dictionary.get("adult_members", 0))
            + (instance.service_price * dictionary.get("members", 0))
        )
        return total_price

    class Meta:
        exclude = (
            "vendor_category",
            "approved",
            "added_by_admin",
        )
        model = Service
