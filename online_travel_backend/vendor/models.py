from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

from administrator.models import User, Category


class Vendor(models.Model):
    vendor = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendor"
    )
    contact_name = models.CharField(max_length=200)
    vendor_name = models.CharField(max_length=200)
    vendor_address = models.CharField(max_length=500)
    vendor_number = models.CharField(max_length=20)
    logo_url = models.URLField()

    def __str__(self) -> str:
        return self.vendor_name


class VendorCategory(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="vendorcategory_vendor"
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


class Service(models.Model):
    vendor_category = models.ForeignKey(
        VendorCategory, on_delete=models.CASCADE, related_name="service_vendorcategory"
    )
    # logging
    created_on = models.DateTimeField(auto_now=True, editable=False)

    # Commons
    service_name = models.CharField(max_length=200)
    image_urls = ArrayField(models.URLField(), default=list, blank=True)
    description = models.CharField(max_length=600)
