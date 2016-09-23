# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ContinentBorder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=2, choices=[(b'AF', 'Africa'), (b'AS', 'Asia'), (b'EU', 'Europe'), (b'NA', 'North America'), (b'SA', 'South America'), (b'OC', 'Oceania'), (b'AN', 'Antarctica')])),
                ('mpoly', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
            options={
                'verbose_name_plural': 'Continent Borders',
            },
        ),
        migrations.CreateModel(
            name='CountryBorder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=2)),
                ('mpoly', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
            options={
                'verbose_name_plural': 'Country Borders',
            },
        ),
    ]
