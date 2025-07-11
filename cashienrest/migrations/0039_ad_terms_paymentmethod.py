# Generated by Django 5.1.7 on 2025-05-30 18:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cashienrest', '0038_transactionrequest_transaction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='ad',
            name='terms',
            field=models.TextField(default='Deafult terms'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment', models.CharField(max_length=30)),
                ('ad_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cashienrest.ad')),
            ],
        ),
    ]
