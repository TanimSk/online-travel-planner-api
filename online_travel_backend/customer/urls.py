from django.urls import path
from .views import CustomerRegistrationView, CreateRfqAPI, RFQTypesAPI

urlpatterns = [
    path(
        "registration/",
        CustomerRegistrationView.as_view(),
        name="customer_registration",
    ),
    path("create_rfq/", CreateRfqAPI.as_view(), name="create_rfq"),
    path("get_rfq/", RFQTypesAPI.as_view(), name="get_rfq"),
    path("get_rfq/<int:rfq_id>", RFQTypesAPI.as_view(), name="get_rfq"),
]
