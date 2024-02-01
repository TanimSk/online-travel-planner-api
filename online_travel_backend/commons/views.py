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
from commons.serializers import CheckHotelSerializer


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
                if type(value) is list:
                    if value:
                        dict[f"{key}__contains"] = value
                    continue

                dict[f"{key}__icontains"] = value

        return dict

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            # keeping all keys instead of non-search params, for searching
            serialized_copy = serialized_data.data.copy()

            # For transportation
            try:
                category_name = Category.objects.get(
                    id=serialized_data.data.get("category_id")
                ).category_name

                if category_name == "Daily Activity Transportation":
                    if serialized_data.data.get(
                        "car_type"
                    ) == "Sedan" and serialized_data.data.get("_members") > (
                        5 * serialized_data.data.get("car_quantity")
                    ):
                        return Response(
                            {
                                "status": "Passenger capacity exceeded for this type of car, please Re-query"
                            },
                            status=400,
                        )

                    elif serialized_data.data.get(
                        "car_type"
                    ) == "SUV" and serialized_data.data.get("_members") > (
                        8 * serialized_data.data.get("car_quantity")
                    ):
                        return Response(
                            {
                                "status": "Passenger capacity exceeded for this type of car, please Re-query"
                            },
                            status=400,
                        )

                    elif serialized_data.data.get(
                        "car_type"
                    ) == "Micro" and serialized_data.data.get("_members") > (
                        12 * serialized_data.data.get("car_quantity")
                    ):
                        return Response(
                            {
                                "status": "Passenger capacity exceeded for this type of car, please Re-query"
                            },
                            status=400,
                        )

                    elif serialized_data.data.get(
                        "car_type"
                    ) == "Mini Bus" and serialized_data.data.get("_members") > (
                        30 * serialized_data.data.get("car_quantity")
                    ):
                        return Response(
                            {
                                "status": "Passenger capacity exceeded for this type of car, please Re-query"
                            },
                            status=400,
                        )

            except Category.DoesNotExist:
                return Response({"status": "Something went wrong"}, status=400)

            for key in [
                "category_id",
                "infant_members",
                "child_members",
                "adult_members",
                "members",
                "check_in_date",
                "check_out_date",
                "duration",
                "depart_time",
                "return_time",
                "car_quantity",
                "quantity",
                "_members",
                "total_room",
                "total_extra_bed",
                "include_breakfast",
            ]:
                try:
                    serialized_copy.pop(key)
                except KeyError:
                    pass

            services_instances = Service.objects.filter(
                vendor_category__category__id=serialized_data.data.get("category_id"),
                approved=True,
                **self.get_search_keys(serialized_copy),
            )
            serialized_services = QueryResultSerializer(
                services_instances,
                many=True,
                context={"dictionary": serialized_data.data, "request": request},
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


class CheckHotelAPI(APIView):
    serializer_class = CheckHotelSerializer

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            category_name = Category.objects.get(
                id=serialized_data.data.get("category_id")
            ).category_name

            if category_name == "Hotel Booking":
                service_instance = Service.objects.get(
                    id=serialized_data.data.get("service_id"),
                    vendor_category__category_id=serialized_data.data.get(
                        "category_id"
                    ),
                )

                # checking capacity of rooms
                has_extra_bed = 0
                if service_instance.extra_bed_price > 0:
                    has_extra_bed = 1

                # show extra beds are available or not
                if (
                    has_extra_bed == 0
                    and serialized_data.data.get("total_extra_bed", 0) > 0
                ):
                    return Response(
                        {"status": "Extra beds are not available for this hotel"},
                        status=400,
                    )

                # validating extra beds
                if serialized_data.data.get("total_room") < serialized_data.data.get(
                    "total_extra_bed"
                ):
                    return Response(
                        {
                            "status": f"You can have maximum {serialized_data.data.get('total_room')} extra beds"
                        },
                        status=400,
                    )

                if (
                    serialized_data.data.get("adult_members")
                    - (
                        service_instance.max_guests
                        * serialized_data.data.get("total_room")
                    )
                    - (serialized_data.data.get("total_extra_bed", 0) * has_extra_bed)
                ) > 0:
                    if has_extra_bed == 1:
                        return Response(
                            {
                                "status": f"Guest Capacity Exceeded, Please Increase Rooms or Extra Beds"
                            },
                            status=400,
                        )
                    else:
                        return Response(
                            {
                                "status": "Guest Capacity Exceeded, Please Increase Rooms"
                            },
                            status=400,
                        )

        return Response()
