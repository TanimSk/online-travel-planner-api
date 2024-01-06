# Generated by Django 4.2.6 on 2024-01-03 07:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=200)),
                ('customer_address', models.CharField(max_length=500)),
                ('customer_number', models.CharField(max_length=20, unique=True)),
                ('added_on', models.DateTimeField(auto_now_add=True)),
                ('confirmed', models.BooleanField(default=False)),
                ('customer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]