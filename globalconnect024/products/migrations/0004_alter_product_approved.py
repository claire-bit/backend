# Generated by Django 5.2.3 on 2025-07-03 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_product_approved_product_stock_product_vendor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='approved',
            field=models.BooleanField(default=True),
        ),
    ]
