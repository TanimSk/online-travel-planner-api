from django.contrib import admin
from .models import Category, User, Bill


@admin.register(Category)
class CateogryAdmin(admin.ModelAdmin):
    list_display = (
        "category_name",
        "image_urls",
        "description",
    )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "is_admin",
        "is_vendor",
        "is_agent",
    )


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_id",
        "vendor",
        "agent",
    )
