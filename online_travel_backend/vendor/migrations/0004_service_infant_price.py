# Generated by Django 4.2.6 on 2023-11-27 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0003_service_adult_price_service_child_price_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='infant_price',
            field=models.FloatField(default=0),
        ),
    ]
