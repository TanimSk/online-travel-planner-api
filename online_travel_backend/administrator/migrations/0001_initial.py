# Generated by Django 4.2.6 on 2023-11-25 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Administrator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin_name', models.CharField(max_length=200)),
                ('mobile_no', models.CharField(max_length=200)),
                ('password_txt', models.CharField(max_length=200)),
            ],
        ),
    ]
