# Generated by Django 5.0.3 on 2024-07-28 12:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("server", "0002_rename_id_backcard_back_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="backcard",
            name="content_type",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="frontcard",
            name="content_type",
            field=models.IntegerField(default=0),
        ),
    ]
