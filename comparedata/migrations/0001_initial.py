# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('random_id', models.CharField(db_index=True, max_length=255, blank=True)),
                ('created_date', models.DateTimeField(null=True, blank=True)),
                ('finished_date', models.DateTimeField(null=True, blank=True)),
                ('status', models.CharField(max_length=255, blank=True)),
                ('error', models.TextField(blank=True)),
                ('object_id', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('object_label', models.CharField(max_length=1000, blank=True)),
                ('object_name', models.CharField(max_length=1000, blank=True)),
                ('fields', models.CharField(max_length=1000, blank=True)),
                ('row_count_org_one', models.IntegerField(null=True, blank=True)),
                ('row_count_org_two', models.IntegerField(null=True, blank=True)),
                ('matching_rows_count_org_one', models.IntegerField(null=True, blank=True)),
                ('matching_rows_count_org_two', models.IntegerField(null=True, blank=True)),
                ('unmatching_rows_count_org_one', models.IntegerField(null=True, blank=True)),
                ('unmatching_rows_count_org_two', models.IntegerField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Object',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255)),
                ('api_name', models.CharField(max_length=255)),
                ('job', models.ForeignKey(to='comparedata.Job')),
            ],
        ),
        migrations.CreateModel(
            name='ObjectField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255)),
                ('api_name', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('object', models.ForeignKey(to='comparedata.Object')),
            ],
        ),
        migrations.CreateModel(
            name='Org',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('org_number', models.PositiveSmallIntegerField()),
                ('access_token', models.CharField(max_length=255)),
                ('instance_url', models.CharField(max_length=255)),
                ('org_id', models.CharField(max_length=255)),
                ('org_name', models.CharField(max_length=255, blank=True)),
                ('username', models.CharField(max_length=255, blank=True)),
                ('status', models.CharField(max_length=255, blank=True)),
                ('error', models.TextField(blank=True)),
                ('job', models.ForeignKey(blank=True, to='comparedata.Job', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UnmatchedRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.TextField()),
                ('job', models.ForeignKey(to='comparedata.Job')),
                ('org', models.ForeignKey(to='comparedata.Org')),
            ],
        ),
    ]
