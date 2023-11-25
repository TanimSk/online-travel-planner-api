# Generated by Django 4.2.6 on 2023-11-25 07:18

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
            ],
        ),
        migrations.CreateModel(
            name='Rfq',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('assigned_on', models.DateTimeField(blank=True, null=True)),
                ('tracking_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('status', models.CharField(choices=[('pending', 'pending'), ('approved', 'approved'), ('assigned', 'assigned'), ('updated', 'updated'), ('declined', 'declined')], default='pending', max_length=20)),
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
                ('date', models.DateTimeField()),
                ('members', models.IntegerField()),
                ('service_price', models.FloatField(default=0)),
                ('rfq_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rfqservice_rfqcategory', to='agent.rfqcategory')),
            ],
        ),
    ]
