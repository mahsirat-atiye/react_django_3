# Generated by Django 2.1.5 on 2019-01-25 13:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0012_auto_20190125_1520'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='footballleague',
            name='game',
        ),
        migrations.AddField(
            model_name='footballgame',
            name='league',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sport.FootballLeague'),
        ),
    ]