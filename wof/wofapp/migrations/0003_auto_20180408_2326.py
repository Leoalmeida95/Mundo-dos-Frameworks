# Generated by Django 2.0 on 2018-04-09 02:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wofapp', '0002_auto_20180408_2324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='perfil',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='wofapp.Perfil'),
            preserve_default=False,
        ),
    ]
