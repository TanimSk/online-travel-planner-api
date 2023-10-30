from django.urls import path
from .views import AgentRegistrationView

urlpatterns = [
    path("registration/", AgentRegistrationView.as_view(), name="agent_registration"),
]
