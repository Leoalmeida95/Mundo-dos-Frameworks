# Generated by Django 2.0 on 2018-05-26 17:23

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('wofapp', '0019_auto_20180526_1347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comentario',
            name='data',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='denuncia',
            name='data',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='data_cadastro',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
