# Generated by Django 4.0.4 on 2022-05-01 05:05

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('idle_buster', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ib_user',
            name='access_token',
            field=models.CharField(max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='ib_user',
            name='ext_id',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AlterField(
            model_name='ib_user',
            name='refresh_token',
            field=models.CharField(max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='ib_user',
            name='timezone',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='ib_user',
            name='yesterday',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='ib_user',
            name='yesterday_mult',
            field=models.FloatField(null=True),
        ),
    ]
