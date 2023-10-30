from django.urls import path
from .views import VendorRegistrationView, ManageServicesAPI

urlpatterns = [
    path("registration/", VendorRegistrationView.as_view(), name="vendor_registration"),
    path("manage_services/", ManageServicesAPI.as_view(), name="manage_services"),
    path(
        "manage_services/<int:service_id>",
        ManageServicesAPI.as_view(),
        name="manage_services",
    ),
]
