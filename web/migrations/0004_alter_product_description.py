# Generated by Django 5.1.4 on 2025-01-11 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_product_color_product_dimension_product_weight_brand_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, default='No description for this product', null=True),
        ),
    ]
