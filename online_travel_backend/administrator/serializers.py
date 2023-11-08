from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import Administrator
from agent.models import Rfq, RfqCategory, RfqService, Agent
from django.conf import settings
from commons.models import Category, User


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
    class Meta:
        model = Agent
        exclude = (
            "id",
            "agent",
        )


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
            "assigned_on",
        )
        model = Rfq


class RfqApproveSerializer(serializers.Serializer):
    approved = serializers.BooleanField(required=True)
