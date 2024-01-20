from django.urls import path
from .views import (
    CustomerRegistrationView,
    CreateRfqAPI,
    RFQTypesAPI,
    GetInvoiceAPI,
    AgentBillsAPI,
    ProfileAPI,
    PackagesAPI
)

urlpatterns = [
    path(
        "registration/",
        CustomerRegistrationView.as_view(),
        name="customer_registration",
    ),
    path("create_rfq/", CreateRfqAPI.as_view(), name="create_rfq"),
    path("get_rfq/", RFQTypesAPI.as_view(), name="get_rfq"),
    path("get_rfq/<int:rfq_id>", RFQTypesAPI.as_view(), name="get_rfq"),
    # package #
    path("get_packages/", PackagesAPI.as_view(), name="get_packages"),
    path("get_packages/<int:package_id>", PackagesAPI.as_view(), name="get_packages"),
    #########
    path("get_invoice/", GetInvoiceAPI.as_view(), name="get_invoice"),
    path(
        "get_invoice/<uuid:rfq_tracing_id>", GetInvoiceAPI.as_view(), name="get_invoice"
    ),
    # bills
    path("bill_requests/", AgentBillsAPI.as_view(), name="bill_requests"),
    # profile
    path("profile/", ProfileAPI.as_view(), name="profile"),
]
