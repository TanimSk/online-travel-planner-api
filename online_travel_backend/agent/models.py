from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from administrator.models import Category
from vendor.models import Service


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


class Rfq(models.Model):
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rfq_agent"
    )
    customer_name = models.CharField(max_length=200)
    customer_address = models.CharField(max_length=200)
    contact_no = models.CharField(max_length=20)
    email_address = models.EmailField()
    travel_date = models.DateTimeField()


class RfqCategory(models.Model):
    rfq = models.ForeignKey(
        Rfq, on_delete=models.CASCADE, related_name="rfqcategory_rfq"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="rfqcategory_category"
    )


class RfqService(models.Model):
    rfq_category = models.ForeignKey(
        Rfq, on_delete=models.CASCADE, related_name="rfqservice_rfqcategory"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="rfqservice_rfqservice"
    )
    # Commons
    date = models.DateTimeField()
    members = models.IntegerField()
