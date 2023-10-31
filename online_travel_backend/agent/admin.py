from django.contrib import admin
from .models import Agent, Rfq, RfqCategory, RfqService


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        "agent_name",
        "agency_name",
        "agent_address",
        "mobile_no",
    )


@admin.register(Rfq)
class RfqAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "customer_address",
        "contact_no",
    )


@admin.register(RfqCategory)
class RfqCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "rfq",
        "category",
    )


@admin.register(RfqService)
class RfqServiceAdmin(admin.ModelAdmin):
    list_display = (
        "rfq_category",
        "service",
    )
