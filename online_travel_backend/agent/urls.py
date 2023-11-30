from django.urls import path
from .views import AgentRegistrationView, CreateRfqAPI, QueryServicesAPI, RFQTypesAPI

urlpatterns = [
    path("registration/", AgentRegistrationView.as_view(), name="agent_registration"),
    path("create_rfq/", CreateRfqAPI.as_view(), name="create_rfq"),
    # Query Services
    path("query_services/", QueryServicesAPI.as_view(), name="query_services"),
    # Rfq
    path("get_rfq/", RFQTypesAPI.as_view(), name="get_rfq"),
    path("get_rfq/<int:rfq_id>", RFQTypesAPI.as_view(), name="get_rfq"),
]
