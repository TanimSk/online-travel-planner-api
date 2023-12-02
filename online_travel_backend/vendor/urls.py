from django.urls import path
from .views import (
    VendorRegistrationView,
    ManageServicesAPI,
    NewTasksAPI,
    RequestBillAPI,
)

urlpatterns = [
    path("registration/", VendorRegistrationView.as_view(), name="vendor_registration"),
    # View/Add Services
    path("manage_services/", ManageServicesAPI.as_view(), name="manage_services"),
    path(
        "manage_services/<int:service_id>",
        ManageServicesAPI.as_view(),
        name="manage_services",
    ),
    # New tasks
    path("new_tasks/", NewTasksAPI.as_view(), name="new_tasks"),
    path("new_tasks/<int:rfq_id>", NewTasksAPI.as_view(), name="new_tasks"),
    # Acounts
    path("request_bill/", RequestBillAPI.as_view(), name="request_bill"),
]
