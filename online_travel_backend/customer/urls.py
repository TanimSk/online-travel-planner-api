from django.urls import path
from .views import CustomerRegistrationView

urlpatterns = [
    path(
        "registration/", CustomerRegistrationView.as_view(), name="customer_registration"
    ),
]
