# Generated by Django 3.2.14 on 2023-11-30 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Members', '0002_memberdata_access_token_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='Payment_Date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='Payment_Status',
            field=models.BooleanField(default=False),
        ),
    ]
