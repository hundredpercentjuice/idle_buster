# Generated by Django 4.0.4 on 2022-05-20 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idle_buster', '0003_rename_created_step_cache_timestamp_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='step_cache',
            name='timestamp',
            field=models.DateTimeField(editable=False),
        ),
    ]