from dj_rest_auth.registration.views import RegisterView
from .serializers import AgentCustomRegistrationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404

from .serializers import RfqServiceSerializer, RfqSerializer
from .models import Rfq, RfqCategory, RfqService


# Authenticate Vendor Only Class
class AuthenticateOnlyAgent(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_agent:
                return True
            else:
                return False
        return False


# Agent Registration
class AgentRegistrationView(RegisterView):
    serializer_class = AgentCustomRegistrationSerializer


class CreateRfqAPI(APIView):
    def get(self, request, format=None, *args, **kwargs):
        return Response(RfqSerializer(Rfq.objects.all().first()).data)


"""
{
    ...rfq,
    category: [],
    services: [
        ...info,
        service_id
    ]
}
"""
