from django.urls import path
from .views import AgentRegistrationView, CreateRfqAPI

urlpatterns = [
    path("registration/", AgentRegistrationView.as_view(), name="agent_registration"),
    path("create_rfq/", CreateRfqAPI.as_view(), name="create_rfq"),
]
