# Generated by Django 4.2.6 on 2024-01-02 05:12

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_name', models.CharField(max_length=200)),
                ('agency_name', models.CharField(max_length=200)),
                ('agent_address', models.CharField(max_length=500)),
                ('mobile_no', models.CharField(max_length=20)),
                ('logo_url', models.URLField()),
                ('trade_license_url', models.URLField()),
                ('commission', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Rfq',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('approved_on', models.DateTimeField(blank=True, null=True)),
                ('tracking_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('total_price', models.FloatField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'pending'), ('approved', 'approved'), ('confirmed', 'confirmed'), ('declined', 'declined'), ('completed', 'completed')], default='pending', max_length=20)),
                ('customer_name', models.CharField(max_length=200)),
                ('customer_address', models.CharField(max_length=200)),
                ('contact_no', models.CharField(max_length=20)),
                ('email_address', models.EmailField(max_length=254)),
                ('travel_date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='RfqCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='RfqService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_status', models.CharField(default='incomplete', max_length=40)),
                ('completed_on', models.DateTimeField(blank=True, null=True)),
                ('tracing_id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('date', models.DateTimeField()),
                ('infant_members', models.IntegerField(default=0)),
                ('child_members', models.IntegerField(default=0)),
                ('adult_members', models.IntegerField(default=0)),
                ('members', models.IntegerField(default=1)),
                ('hotel_name', models.CharField(blank=True, max_length=300, null=True)),
                ('room_type', models.CharField(blank=True, max_length=300, null=True)),
                ('bed_type', models.CharField(blank=True, max_length=300, null=True)),
                ('check_in_date', models.DateTimeField(blank=True, null=True)),
                ('check_out_date', models.DateTimeField(blank=True, null=True)),
                ('from_area', models.CharField(blank=True, max_length=300, null=True)),
                ('to_area', models.CharField(blank=True, max_length=300, null=True)),
                ('flight_class', models.CharField(blank=True, max_length=300, null=True)),
                ('trip_type', models.CharField(blank=True, max_length=300, null=True)),
                ('depart_time', models.CharField(blank=True, max_length=300, null=True)),
                ('return_time', models.CharField(blank=True, max_length=300, null=True)),
                ('event_type', models.CharField(blank=True, max_length=300, null=True)),
                ('event_venue', models.CharField(blank=True, max_length=300, null=True)),
                ('day_type', models.CharField(blank=True, max_length=300, null=True)),
                ('transfer_type', models.CharField(blank=True, max_length=300, null=True)),
                ('car_type', models.CharField(blank=True, max_length=300, null=True)),
                ('service_price', models.FloatField(default=0)),
                ('admin_commission', models.FloatField(default=0)),
                ('agent_commission', models.FloatField(default=0)),
                ('rfq_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rfqservice_rfqcategory', to='agent.rfqcategory')),
            ],
        ),
    ]
