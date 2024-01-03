from django.shortcuts import render
from .serializers import CustomerCustomRegistrationSerializer
from rest_framework.permissions import BasePermission
from dj_rest_auth.registration.views import RegisterView


# Authenticate Agent Only Class
class AuthenticateOnlyCustomer(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_customer:
                return True
            else:
                return False
        return False


# Agent Registration
class CustomerRegistrationView(RegisterView):
    serializer_class = CustomerCustomRegistrationSerializer


