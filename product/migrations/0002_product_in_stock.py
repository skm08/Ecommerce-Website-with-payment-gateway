# Generated by Django 4.1 on 2023-09-29 15:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="in_stock",
            field=models.BooleanField(default=True),
        ),
    ]