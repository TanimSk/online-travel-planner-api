from django.db import models
from django.conf import settings


def get_default_access_routes():
    return [
        {"path": "/dashboard/admin/admin-overview"},
        {"path": "/dashboard/admin/qoutation"},
        {"path": "/dashboard/admin/assign-service-provider"},
        {"path": "/dashboard/admin/assigned-service-provider"},
        {"path": "/dashboard/admin/list-of-orders"},
        {"path": "/dashboard/admin/update-orders"},
        {"path": "/dashboard/admin/manage-service"},
        {"path": "/dashboard/admin/requested-services"},
        {"path": "/dashboard/admin/requested-registration/vendor"},
        {"path": "/dashboard/admin/requested-registration/agent"},
        {"path": "/dashboard/admin/requested-registration/customer"},
        {"path": "/dashboard/admin/approved-registration"},
        {"path": "/dashboard/admin/create-service"},
        {"path": "/dashboard/admin/admin-service"},
        {"path": "/dashboard/admin/task-list"},
        {"path": "/dashboard/admin/all-bills"},
        {"path": "/dashboard/admin/bills-paid"},
        {"path": "/dashboard/admin/bills-paid-vendor-by-admin"},
        {"path": "/dashboard/admin/recieved-payments-from-agent"},
        {"path": "/dashboard/admin/bills-req-vendor"},
    ]


class Administrator(models.Model):
    administrator = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="administrator"
    )
    admin_name = models.CharField(max_length=200)
    mobile_no = models.CharField(max_length=200)
    password_txt = models.CharField(max_length=200)

    access_routes = models.JSONField(default=get_default_access_routes)
    

    def __str__(self) -> str:
        return self.admin_name
