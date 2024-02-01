from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from commons.models import Category
from vendor.models import Service
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
import uuid


class Agent(models.Model):
    agent = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent"
    )
    agent_name = models.CharField(max_length=200, blank=True, null=True)
    agency_name = models.CharField(max_length=200, blank=True, null=True)
    agent_address = models.CharField(max_length=500, blank=True, null=True)
    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    trade_license_url = models.URLField(blank=True, null=True)

    # For customers
    pseudo_agent = models.BooleanField(default=False)

    # Money
    commission = models.FloatField(default=0)

    # Tracing
    registered_on = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self) -> str:
        return self.agency_name


class Rfq(models.Model):
    # For Agent
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rfq_agent",
        null=True,
        blank=True,
    )

    # For Customer
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rfq_customer",
        null=True,
        blank=True,
    )

    # tracing
    created_on = models.DateTimeField(default=timezone.now, editable=False)
    approved_on = models.DateTimeField(blank=True, null=True)
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False)
    total_price = models.FloatField(blank=True, null=True)

    STATUS = (
        ("pending", "pending"),
        ("approved", "approved"),
        ("confirmed", "confirmed"),
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
        return self.rfqcategory_rfq.all().order_by("-id")

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
        return self.rfqservice_rfqcategory.all().order_by("-id")


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
        ("dispatched", "dispatched"),
    )
    order_status = models.CharField(max_length=40, default="incomplete")
    completed_on = models.DateTimeField(blank=True, null=True)
    tracing_id = models.UUIDField(default=uuid.uuid4, unique=True)
    remarks = models.TextField(blank=True, null=True)

    # Commons
    travel_time = models.DateTimeField(blank=True, null=True)
    infant_members = models.IntegerField(default=0, blank=True, null=True)
    child_members = models.IntegerField(default=0, blank=True, null=True)
    adult_members = models.IntegerField(default=0, blank=True, null=True)
    members = models.IntegerField(default=0, blank=True, null=True)
    area_name = models.CharField(blank=True, null=True, max_length=500)
    quantity = models.IntegerField(default=0, blank=True, null=True)

    # Hotel
    # hotel_name = models.CharField(max_length=300, blank=True, null=True)
    room_type = models.CharField(max_length=300, blank=True, null=True)
    bed_type = models.CharField(max_length=300, blank=True, null=True)
    check_in_date = models.DateTimeField(blank=True, null=True)
    check_out_date = models.DateTimeField(blank=True, null=True)
    total_room = models.IntegerField(default=0)
    total_extra_bed = models.IntegerField(default=0)
    include_breakfast = models.BooleanField(default=False)

    # Area
    from_area = models.CharField(max_length=300, blank=True, null=True)
    to_area = models.CharField(max_length=300, blank=True, null=True)

    # Flight
    flight_class = models.CharField(max_length=300, blank=True, null=True)
    trip_type = models.CharField(max_length=300, blank=True, null=True)
    depart_time = models.DateTimeField(blank=True, null=True)
    return_time = models.DateTimeField(blank=True, null=True)

    # Venue sourcing
    event_type = models.CharField(max_length=300, blank=True, null=True)
    event_venue = models.CharField(max_length=300, blank=True, null=True)

    # Sight Seeing
    day_type = models.CharField(max_length=300, blank=True, null=True)
    transfer_type = models.CharField(max_length=300, blank=True, null=True)

    # Transportation
    car_type = models.CharField(max_length=300, blank=True, null=True)
    car_quantity = models.IntegerField(default=0, blank=True, null=True)

    # AV production
    duration = models.IntegerField(default=0, blank=True, null=True)

    # Package
    services_name = ArrayField(models.CharField(), default=list, blank=True, null=True)

    #  ---- Prices ----
    # Calculate price, when placing rfq order
    service_price = models.FloatField(default=0)
    base_price = models.FloatField(default=0)
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
        == services_instance.filter(order_status="dispatched").count()
    )

    # If all services are complete, update the Rfq status to 'completed'
    if all_services_complete:
        instance.rfq_category.rfq.status = "completed"
        instance.rfq_category.rfq.save()
