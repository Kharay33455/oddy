# Generated by Django 5.1.7 on 2025-05-12 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cashienrest', '0003_trade'),
    ]

    operations = [
        migrations.AddField(
            model_name='trade',
            name='currency',
            field=models.CharField(default=1, max_length=1),
            preserve_default=False,
        ),
    ]
