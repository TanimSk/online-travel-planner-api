# Generated by Django 4.2.6 on 2023-11-20 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0002_alter_vendorcategory_vendor'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='added_by_admin',
            field=models.BooleanField(default=False),
        ),
    ]
