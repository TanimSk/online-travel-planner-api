# Generated by Django 4.2.6 on 2023-11-30 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0004_service_infant_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='admin_commission',
            field=models.FloatField(default=0),
        ),
    ]
