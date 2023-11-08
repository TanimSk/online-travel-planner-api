from django.db import models
from django.conf import settings


class Administrator(models.Model):
    administrator = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="administrator"
    )
    admin_name = models.CharField(max_length=200)
    mobile_no = models.CharField(max_length=200)
    password_txt = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.admin_name
