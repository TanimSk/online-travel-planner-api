# Generated by Django 4.2.6 on 2023-11-19 13:53

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('commons', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contact_name', models.CharField(max_length=200)),
                ('vendor_name', models.CharField(max_length=200)),
                ('vendor_address', models.CharField(max_length=500)),
                ('vendor_number', models.CharField(max_length=20)),
                ('logo_url', models.URLField()),
                ('added_on', models.DateTimeField(auto_now_add=True)),
                ('approved', models.BooleanField(default=False)),
                ('vendor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vendor', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='VendorCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendorcategory_category', to='commons.category')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendorcategory_vendor', to='vendor.vendor')),
            ],
            options={
                'unique_together': {('vendor', 'category')},
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('approved', models.BooleanField(default=False)),
                ('service_name', models.CharField(blank=True, max_length=200, null=True)),
                ('image_urls', django.contrib.postgres.fields.ArrayField(base_field=models.URLField(), blank=True, default=list, null=True, size=None)),
                ('description', models.CharField(blank=True, max_length=600, null=True)),
                ('area_name', models.CharField(blank=True, max_length=500, null=True)),
                ('hotel_name', models.CharField(blank=True, max_length=300, null=True)),
                ('room_type', models.CharField(blank=True, max_length=300, null=True)),
                ('bed_type', models.CharField(blank=True, max_length=300, null=True)),
                ('from_area', models.CharField(blank=True, max_length=500, null=True)),
                ('to_area', models.CharField(blank=True, max_length=500, null=True)),
                ('flight_class', models.CharField(blank=True, max_length=200, null=True)),
                ('trip_type', models.CharField(blank=True, max_length=200, null=True)),
                ('depart_time', models.DateTimeField(blank=True, null=True)),
                ('return_time', models.DateTimeField(blank=True, null=True)),
                ('event_type', models.CharField(blank=True, max_length=200, null=True)),
                ('event_venue', models.CharField(blank=True, max_length=200, null=True)),
                ('day_type', models.CharField(blank=True, max_length=200, null=True)),
                ('transfer_type', models.CharField(blank=True, max_length=200, null=True)),
                ('duration', models.FloatField(blank=True, null=True)),
                ('car_type', models.CharField(blank=True, null=True)),
                ('vendor_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_vendorcategory', to='vendor.vendorcategory')),
            ],
        ),
    ]
