from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid


class User(AbstractUser):
    # Boolean fields to select the type of account.
    is_admin = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)

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
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False)

    # bill owners
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bill_vendor"
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bill_agent"
    )
    service = models.OneToOneField(
        "agent.RfqService", on_delete=models.CASCADE, related_name="bill_service"
    )

    # status
    STATUS_1 = (
        ("agent_paid", "agent_paid"),
        ("admin_paid", "admin_paid"),
    )

    STATUS_2 = (
        ("vendor_bill", "vendor_bill"),
        ("admin_bill", "admin_bill"),
        ("vendor_paid", "vendor_paid"),
    )

    status_1 = models.CharField(choices=STATUS_1, default="agent_paid", max_length=20)
    status_2 = models.CharField(choices=STATUS_2, default="vendor_bill", max_length=20)

    # dates
    created_on = models.DateTimeField(auto_now_add=True)
    admin_billed_on = models.DateTimeField(blank=True, null=True)
    # agent_billed_on = models.DateTimeField(blank=True, null=True)

    admin_paid_on = models.DateTimeField(blank=True, null=True)
    vendor_paid_on = models.DateTimeField(blank=True, null=True)

    # money
    vendor_bill = models.FloatField()
    admin_bill = models.FloatField()
    agent_bill = models.FloatField()

    # due
    agent_due = models.FloatField(default=0)
    admin_due = models.FloatField(default=0)

    # payment type
    PAYMENT_TYPE = (
        ("cash", "cash"),
        ("account_transfer", "account_transfer"),
    )
    admin_payment_type = models.CharField(choices=PAYMENT_TYPE, default="cash")
    vendor_payment_type = models.CharField(choices=PAYMENT_TYPE, default="cash")
