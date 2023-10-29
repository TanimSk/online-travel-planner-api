from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

from administrator.models import User, Category


class Vendor(models.Model):
    vendor = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendor"
    )
    logo_url = models.URLField()
    contact_name = models.CharField(max_length=200)
    vendor_name = models.CharField(max_length=200)
    vendor_address = models.CharField(max_length=500)
    vendor_number = models.CharField(max_length=20)


class VendorCategory(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="vendorcategory_vendor"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="vendorcategory_category"
    )


class Service(models.Model):
    vendor_category = models.ForeignKey(
        VendorCategory, on_delete=models.CASCADE, related_name="service_vendorcategory"
    )

    # Commons
    service_name = models.CharField(max_length=200)
    image_urls = ArrayField(models.URLField(), default=list, blank=True)
    description = models.CharField(max_length=600)
