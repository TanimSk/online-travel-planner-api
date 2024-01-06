from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from dj_rest_auth.registration.views import RegisterView
from .serializers import CustomerCustomRegistrationSerializer, RfqSerializer


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


# Create RFQ
class CreateRfqAPI(APIView):
    serializer_class = RfqSerializer
    permission_classes = [AuthenticateOnlyCustomer]

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(
            data=request.data, context={"request": request, "total_price": False}
        )

        if serialized_data.is_valid(raise_exception=True):
            if request.GET.get("get_price") == "true":
                return Response(serialized_data.calc_total_price(serialized_data.data))

            rfq_instance = serialized_data.create(serialized_data.data)
            rfq_instance.save()

            return Response({"status": "Successfully created RFQ"})

# 