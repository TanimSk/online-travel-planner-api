from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import Agent


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


