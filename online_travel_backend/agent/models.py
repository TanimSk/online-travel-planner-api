from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from commons.models import Category
from vendor.models import Service
import uuid


class Agent(models.Model):
    agent = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent"
    )
    agent_name = models.CharField(max_length=200)
    agency_name = models.CharField(max_length=200)
    agent_address = models.CharField(max_length=500)
    mobile_no = models.CharField(max_length=20)
    logo_url = models.URLField()
    trade_license_url = models.URLField()

    # Money
    commission = models.FloatField(default=0)

    def __str__(self) -> str:
        return self.agency_name


class Rfq(models.Model):
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rfq_agent"
    )

    # tracing
    created_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(blank=True, null=True)
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False)

    STATUS = (
        ("pending", "pending"),
        ("approved", "approved"),
        ("declined", "declined"),
        ("completed", "completed"),
    )
    status = models.CharField(choices=STATUS, max_length=20, default="pending")

    customer_name = models.CharField(max_length=200)
    customer_address = models.CharField(max_length=200)
    contact_no = models.CharField(max_length=20)
    email_address = models.EmailField()
    travel_date = models.DateTimeField()

    def __str__(self) -> str:
        return f"RFQ | {self.email_address}"

    @property
    def rfq_categories(self):
        return self.rfqcategory_rfq.all()

    @property
    def agent_info(self):
        return self.agent.agent


class RfqCategory(models.Model):
    rfq = models.ForeignKey(
        Rfq, on_delete=models.CASCADE, related_name="rfqcategory_rfq"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="rfqcategory_category"
    )

    def __str__(self) -> str:
        return f"{self.rfq.email_address} | {self.category.category_name}"

    @property
    def rfq_services(self):
        return self.rfqservice_rfqcategory.all()


class RfqService(models.Model):
    rfq_category = models.ForeignKey(
        RfqCategory, on_delete=models.CASCADE, related_name="rfqservice_rfqcategory"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="rfqservice_rfqservice",
        blank=True,
        null=True,
    )

    # Tracing
    STATUS = (
        ("incomplete", "incomplete"),
        ("processing", "processing"),
        ("complete", "complete"),
        ("complete_admin", "complete_admin"),
        ("complete_agent", "complete_agent"),
    )
    order_status = models.CharField(max_length=40, default="incomplete")
    completed_on = models.DateTimeField(blank=True, null=True)

    # Commons
    date = models.DateTimeField()
    infant_members = models.IntegerField(default=0)
    child_members = models.IntegerField(default=0)
    adult_members = models.IntegerField(default=0)
    members = models.IntegerField(default=1)

    #  ---- Prices ----
    # Calculate price, when placing rfq order
    service_price = models.FloatField(default=0)
    admin_commission = models.FloatField(default=0)
    agent_commission = models.FloatField(default=0)


@receiver(post_save, sender=RfqService)
def update_rfq_status(sender, instance, **kwargs):
    # Check if all services related to the Rfq are complete

    services_instance = RfqService.objects.filter(
        rfq_category__rfq=instance.rfq_category.rfq
    )

    all_services_complete = (
        services_instance.count()
        == services_instance.filter(order_status="complete").count()
    )

    # If all services are complete, update the Rfq status to 'completed'
    if all_services_complete:
        instance.rfq_category.rfq.status = "completed"
        instance.rfq_category.rfq.save()
