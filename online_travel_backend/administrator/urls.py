from django.urls import path
from .views import AdminRegistrationView, PendingRfqAPI, CategoryAPI, ApprovedRfqAPI

urlpatterns = [
    path("registration/", AdminRegistrationView.as_view(), name="admin_registration"),
    path("create_category/", CategoryAPI.as_view(), name="create_category"),
    # Pending RFQ
    path("pending_rfq/", PendingRfqAPI.as_view(), name="pending_rfq"),
    path("pending_rfq/<int:rfq_id>", PendingRfqAPI.as_view(), name="pending_rfq"),
    # Orders
    path("approved_rfq/", ApprovedRfqAPI.as_view(), name="approved_rfq"),
    path("approved_rfq/<int:rfq_id>", ApprovedRfqAPI.as_view(), name="approved_rfq"),

    
]
