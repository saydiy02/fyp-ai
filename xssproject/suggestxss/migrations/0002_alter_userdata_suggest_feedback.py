# Generated by Django 5.0.4 on 2024-05-29 08:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('suggestxss', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdata',
            name='suggest',
            field=models.IntegerField(choices=[(0, 'Nmap & OWASP ZAP'), (1, 'Nmap & XSSer')]),
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agree', models.BooleanField()),
                ('user_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='suggestxss.userdata')),
            ],
        ),
    ]
