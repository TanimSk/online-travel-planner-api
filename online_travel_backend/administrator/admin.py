from django.contrib import admin
from .models import Category, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "is_admin",
        "is_vendor",
        "is_agent",
    )


@admin.register(Category)
class CateogryAdmin(admin.ModelAdmin):
    list_display = (
        "category_name",
        "image_urls",
        "description",
    )
