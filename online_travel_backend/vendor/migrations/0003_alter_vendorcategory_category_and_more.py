# Generated by Django 4.2.6 on 2023-10-30 08:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0003_remove_category_adminisitrator'),
        ('vendor', '0002_alter_vendorcategory_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorcategory',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendorcategory_category', to='administrator.category'),
        ),
        migrations.AlterUniqueTogether(
            name='vendorcategory',
            unique_together={('vendor', 'category')},
        ),
    ]
