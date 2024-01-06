from django.urls import path
from .views import CustomerRegistrationView, CreateRfqAPI

urlpatterns = [
    path(
        "registration/", CustomerRegistrationView.as_view(), name="customer_registration"
    ),    
    path(
        "create_rfq/", CreateRfqAPI.as_view(), name="create_rfq"
    ),
]
