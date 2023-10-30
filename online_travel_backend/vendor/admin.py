from django.contrib import admin
from .models import VendorCategory, Service, Vendor


@admin.register(Vendor)
class VendorCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "vendor",
        "contact_name",
        "vendor_name",
    )


@admin.register(VendorCategory)
class VendorCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "vendor",
        "category",
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "vendor_category",
        "service_name",
        "image_urls",
        "description",
    )
