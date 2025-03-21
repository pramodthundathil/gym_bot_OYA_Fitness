# Generated by Django 4.2.7 on 2023-12-20 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Members', '0006_accesstogate_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='Mode_of_Payment',
            field=models.CharField(blank=True, choices=[('Cash', 'Cash'), ('Bank Transfer', 'Bank Transfer'), ('Card', 'Card')], max_length=255, null=True),
        ),
    ]
