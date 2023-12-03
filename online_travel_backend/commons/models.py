from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    # Boolean fields to select the type of account.
    is_admin = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.email


class Category(models.Model):
    category_name = models.CharField(max_length=200)
    image_urls = ArrayField(models.URLField(), default=list, blank=True)
    description = models.CharField(max_length=500)

    def __str__(self) -> str:
        return self.category_name


class Bill(models.Model):
    # pointed to RfqService
    tracking_id = models.UUIDField()

    # bill owners
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bill_vendor"
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bill_agent"
    )

    # status
    STATUS = (
        ("vendor_bill", "vendor_bill"),
        ("admin_bill", "admin_bill"),
        ("agent_bill", "agent_bill"),
        # ("agent_paid", "agent_paid"),
        ("admin_paid", "admin_paid"),
        ("vendor_paid", "vendor_paid"),
    )
    status = models.CharField(choices=STATUS, default="vendor_bill", max_length=20)

    # dates
    created_on = models.DateTimeField(auto_now_add=True)
    admin_billed_on = models.DateTimeField(blank=True, null=True)
    agent_billed_on = models.DateTimeField(blank=True, null=True)

    admin_paid_on = models.DateTimeField(blank=True, null=True)
    vendor_paid_on = models.DateTimeField(blank=True, null=True)

    # money
    vendor_bill = models.FloatField()
    admin_bill = models.FloatField()
    agent_bill = models.FloatField()

    # payment type
    PAYMENT_TYPE = (
        ("cash", "cash"),
        ("account_transfer", "account_transfer"),
    )
    admin_payment_type = models.CharField(choices=PAYMENT_TYPE, default="cash")
    vendor_payment_type = models.CharField(choices=PAYMENT_TYPE, default="cash")
