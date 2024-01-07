from .serializers import CategorySerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from dj_rest_auth.registration.views import LoginView
from django.contrib.auth import login as django_login
from .models import Category


from vendor.models import Service
from agent.serializers import (
    QueryServiceSerializer,
    QueryResultSerializer,
    ServiceInfo,
    SuggestionSerializer,
)


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

        elif self.user.is_customer:
            if self.user.customer.confirmed:
                django_login(self.request, self.user)
            else:
                return Response({"error": "Your account is not verified"})

        return self.get_response()


class CategoriesAPI(APIView):
    serializer_class = CategorySerializer

    def get(self, request, format=None, *args, **kwargs):
        instance = Category.objects.all()
        serialized_data = CategorySerializer(instance, many=True)
        return Response(serialized_data.data)


# Query Service
class QueryServicesAPI(APIView):
    serializer_class = QueryServiceSerializer

    def get_search_keys(self, data):
        dict = {}
        for key, value in data.items():
            if not (value == "" or value is None):
                dict[f"{key}__icontains"] = value

        return dict

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            # keeping all keys instead of non-search params, for searching
            serialized_copy = serialized_data.data.copy()

            for key in [
                "category_id",
                "infant_members",
                "child_members",
                "adult_members",
                "members",

            ]:
                serialized_copy.pop(key)

            services_instances = Service.objects.filter(
                vendor_category__category__id=serialized_data.data.get("category_id"),
                approved=True,
                **self.get_search_keys(serialized_copy),
            )
            serialized_services = QueryResultSerializer(
                services_instances,
                many=True,
                context={"dictionary": serialized_data.data},
            )
            return Response(serialized_services.data)

    def get(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            return Response({"error": "Service id is missing"})

        service_instance = Service.objects.get(id=service_id)
        return Response(ServiceInfo(service_instance).data)


# Suggestion API
class SuggestionAPI(APIView):
    serializer_class = SuggestionSerializer

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            dict = {}
            dict[
                f"{serialized_data.data.get('field_name')}__icontains"
            ] = serialized_data.data.get("field_content")
            suggestions = (
                Service.objects.filter(
                    vendor_category__category_id=serialized_data.data.get(
                        "category_id"
                    ),
                    **dict,
                )
                .values_list(serialized_data.data.get("field_name"), flat=True)
                .distinct()[:15]
            )
            return Response(suggestions)
