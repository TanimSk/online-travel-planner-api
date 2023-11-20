from .serializers import CategorySerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from dj_rest_auth.registration.views import LoginView
from django.contrib.auth import login as django_login
from .models import Category


# Login
class LoginWthPermission(LoginView):
    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(data=self.request.data)
        self.serializer.is_valid(raise_exception=True)

        self.login()

        if self.user.is_vendor:
            if self.user.vendor.approved:
                django_login(self.request, self.user)
            else:
                return Response({"error": "Your account has not been approved"})

        return self.get_response()


class CategoriesAPI(APIView):
    serializer_class = CategorySerializer

    def get(self, request, format=None, *args, **kwargs):
        instance = Category.objects.all()
        serialized_data = CategorySerializer(instance, many=True)
        return Response(serialized_data.data)
