# Generated by Django 2.1.5 on 2019-01-28 07:32

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0018_auto_20190128_1049'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basketballplayer',
            name='post',
            field=models.CharField(choices=[('G', 'گارد'), ('C', 'مرکز'), ('GF', 'گارد فوروارد'), ('FG', 'فوروارد گارد'), ('FC', 'فوروارد سنتر')], max_length=2),
        ),
        migrations.AlterField(
            model_name='basketballteam',
            name='followers',
            field=models.ManyToManyField(blank=True, null=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
