from django.db import models
from django.conf import settings


class Customer(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer"
    )

    customer_name = models.CharField(max_length=200)
    customer_address = models.CharField(max_length=500)
    customer_number = models.CharField(max_length=20, unique=True)

    # tracing
    added_on = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.vendor_name
