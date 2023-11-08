from django.contrib import admin
from .models import Administrator


@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = (
        "admin_name",
        "mobile_no",
    )
