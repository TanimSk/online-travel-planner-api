from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    # Boolean fields to select the type of account.
    is_admin = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)


class Category(models.Model):
    adminisitrator = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="category_admin",
    )
    category_name = models.CharField(max_length=200)
    image_urls = ArrayField(models.URLField(), default=list, blank=True)
    description = models.CharField(max_length=500)
