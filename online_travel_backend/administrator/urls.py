from django.urls import path
from .views import (
    AdminRegistrationView,
    PendingRfqAPI,
    CategoryAPI,
    ApprovedRfqAPI,
    VendorListAPI,
    RequestedVendorAPI,
    ManageServicesAPI,
    ManageVendorServicesAPI,
    AssignAgentAPI,
    AgentBillAPI,
    VendorBillAPI,
    TaskListAPI,
    VendorRegistrationView,
    AgentListAPI,
    OverviewAPI,
    AdminRoleAPI,
)

urlpatterns = [
    path("registration/", AdminRegistrationView.as_view(), name="admin_registration"),
    path("overview/", OverviewAPI.as_view(), name="overview_api"),
    path(
        "add_service_provider/",
        VendorRegistrationView.as_view(),
        name="vendor_registration",
    ),
    path("create_category/", CategoryAPI.as_view(), name="create_category"),
    # Pending RFQ
    path("pending_rfq/", PendingRfqAPI.as_view(), name="pending_rfq"),
    path("pending_rfq/<int:rfq_id>", PendingRfqAPI.as_view(), name="pending_rfq"),
    # Orders
    path("approved_rfq/", ApprovedRfqAPI.as_view(), name="approved_rfq"),
    path("approved_rfq/<int:rfq_id>", ApprovedRfqAPI.as_view(), name="approved_rfq"),
    # Vendors
    path("vendors/", VendorListAPI.as_view(), name="vendor_list"),
    path("vendors/<int:vendor_id>", VendorListAPI.as_view(), name="vendor_list"),
    path("requested_vendors/", RequestedVendorAPI.as_view(), name="requested_vendor"),
    path(
        "requested_vendors/<int:vendor_id>",
        RequestedVendorAPI.as_view(),
        name="requested_vendor",
    ),
    # manage services
    path(
        "pending_services/",
        ManageVendorServicesAPI.as_view(),
        name="manage_admin_services",
    ),
    path(
        "pending_services/<int:service_id>",
        ManageVendorServicesAPI.as_view(),
        name="manage_admin_services",
    ),
    path("manage_services/", ManageServicesAPI.as_view(), name="manage_admin_services"),
    path(
        "manage_services/<int:service_id>",
        ManageServicesAPI.as_view(),
        name="manage_admin_services",
    ),
    # list of agents
    path("agents/", AgentListAPI.as_view(), name="agent_list"),
    path("agents/<int:agent_id>", AgentListAPI.as_view(), name="agent_list"),
    # assigning vendors
    path("assign_agents/", AssignAgentAPI.as_view(), name="assign_agents"),
    path("task_lists/", TaskListAPI.as_view(), name="task_lists"),
    # update order api
    path("agent_bills/", AgentBillAPI.as_view(), name="agent_bill"),
    path("vendor_bills/", VendorBillAPI.as_view(), name="vendor_bill"),
    # role management
    path("admin_roles/", AdminRoleAPI.as_view(), name="admin_roles"),
]
