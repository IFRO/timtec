# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import re


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_auto_20161207_1830'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timtecuser',
            name='city',
            field=models.CharField(max_length=64, verbose_name='City', blank=True),
        ),
        migrations.AlterField(
            model_name='timtecuser',
            name='first_name',
            field=models.CharField(max_length=64, verbose_name='First name', blank=True),
        ),
        migrations.AlterField(
            model_name='timtecuser',
            name='last_name',
            field=models.CharField(max_length=64, verbose_name='Last name', blank=True),
        ),
        migrations.AlterField(
            model_name='timtecuser',
            name='occupation',
            field=models.CharField(max_length=64, verbose_name='Occupation', blank=True),
        ),
        migrations.AlterField(
            model_name='timtecuser',
            name='username',
            field=models.CharField(help_text='Required. 128 characters or fewer. Letters, numbers and ./+/-/_ characters', unique=True, max_length=128, verbose_name='Username', validators=[django.core.validators.RegexValidator(re.compile(b'^[\\w.+-]+$'), 'Enter a valid username.', b'invalid')]),
        ),
    ]
