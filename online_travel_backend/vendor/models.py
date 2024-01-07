from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
import uuid
from commons.models import Category


class Vendor(models.Model):
    vendor = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendor"
    )

    contact_name = models.CharField(max_length=200)
    vendor_name = models.CharField(max_length=200)
    vendor_address = models.CharField(max_length=500)
    vendor_number = models.CharField(max_length=20)
    logo_url = models.URLField()

    password_text = models.CharField(blank=True, null=True, max_length=300)

    # tracing
    added_on = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.vendor_name

    @property
    def vendor_categories(self):
        return self.vendorcategory_vendor.all()


class VendorCategory(models.Model):
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="vendorcategory_vendor",
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="vendorcategory_category"
    )

    class Meta:
        unique_together = (
            "vendor",
            "category",
        )

    def __str__(self) -> str:
        return self.category.category_name

    @property
    def vendor_services(self):
        return self.service_vendorcategory.all()


class Service(models.Model):
    vendor_category = models.ForeignKey(
        VendorCategory, on_delete=models.CASCADE, related_name="service_vendorcategory"
    )
    # tracing
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
    added_by_admin = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)  # service should be approved by admin
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False)

    # Commons
    service_name = models.CharField(max_length=200, blank=True, null=True)
    image_urls = ArrayField(models.URLField(), default=list, blank=True, null=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    overview = models.CharField(max_length=1000, blank=True, null=True)
    itinerary = models.CharField(max_length=1000, blank=True, null=True)
    rates = models.CharField(max_length=1000, blank=True, null=True)

    # money
    infant_price = models.FloatField(default=0)
    child_price = models.FloatField(default=0)
    adult_price = models.FloatField(default=0)
    service_price = models.FloatField(default=0)
    cost_per_hour = models.FloatField(default=0)
    admin_commission = models.FloatField(default=0)


    # venue sourcing
    area_name = models.CharField(max_length=500, blank=True, null=True)

    # hotel booking
    # hotel_name = models.CharField(max_length=300, blank=True, null=True)
    room_type = models.CharField(max_length=300, blank=True, null=True)
    bed_type = models.CharField(max_length=300, blank=True, null=True)

    # flight booking + transportation
    from_area = models.CharField(max_length=500, blank=True, null=True)
    to_area = models.CharField(max_length=500, blank=True, null=True)

    # flight booking
    flight_class = models.CharField(max_length=200, blank=True, null=True)
    trip_type = models.CharField(max_length=200, blank=True, null=True)
    depart_time = models.DateTimeField(blank=True, null=True)
    return_time = models.DateTimeField(blank=True, null=True)

    # entertainment - v
    # meeting and event management - v
    # special activities

    # event decoration
    event_type = models.CharField(max_length=200, blank=True, null=True)
    event_venue = models.CharField(max_length=200, blank=True, null=True)

    # sight seeing
    day_type = models.CharField(max_length=200, blank=True, null=True)
    transfer_type = models.CharField(max_length=200, blank=True, null=True)

    # AV production
    duration = models.FloatField(blank=True, null=True)

    # daily transportation
    car_type = models.CharField(blank=True, null=True)

    def __str__(self) -> str:
        return self.service_name
