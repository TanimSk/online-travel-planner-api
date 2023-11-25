from django.urls import path
from .views import AgentRegistrationView, CreateRfqAPI, QueryServicesAPI

urlpatterns = [
    path("registration/", AgentRegistrationView.as_view(), name="agent_registration"),
    path("create_rfq/", CreateRfqAPI.as_view(), name="create_rfq"),
    # Query Services
    path("query_services/", QueryServicesAPI.as_view(), name="query_services"),
]
