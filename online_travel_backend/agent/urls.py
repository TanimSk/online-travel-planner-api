from django.urls import path
from .views import (
    AgentRegistrationView,
    CreateRfqAPI,
    RFQTypesAPI,
    GetInvoiceAPI,
    RequestBillAPI,
    OverviewAPI,
    BillPayAPI,
    SetCommissionAPI,
)

urlpatterns = [
    path("registration/", AgentRegistrationView.as_view(), name="agent_registration"),
    path("create_rfq/", CreateRfqAPI.as_view(), name="create_rfq"),
    path("overview/", OverviewAPI.as_view(), name="overview_api"),
    # Rfq
    path("get_rfq/", RFQTypesAPI.as_view(), name="get_rfq"),
    path("get_rfq/<int:rfq_id>", RFQTypesAPI.as_view(), name="get_rfq"),
    # invoice
    path("get_invoice/", GetInvoiceAPI.as_view(), name="get_invoice"),
    path(
        "get_invoice/<uuid:rfq_tracing_id>", GetInvoiceAPI.as_view(), name="get_invoice"
    ),
    # bills
    path("get_bills/", RequestBillAPI.as_view(), name="bill_requests"),
    path("pay_bill/", BillPayAPI.as_view(), name="pay_bill"),
    path("set_commission/", SetCommissionAPI.as_view(), name="set_commission"),
]
