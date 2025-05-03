from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('companies', '0001_initial'),
        ('sentinelvision', '0004_add_feed_execution_record'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnrichedIOC',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('ioc_type', models.CharField(choices=[('ip', 'IP Address'), ('domain', 'Domain'), ('url', 'URL'), ('md5', 'MD5 Hash'), ('sha1', 'SHA1 Hash'), ('sha256', 'SHA256 Hash'), ('email', 'Email Address'), ('cve', 'CVE'), ('filename', 'Filename'), ('filepath', 'Filepath'), ('registry', 'Registry Key'), ('other', 'Other')], max_length=20, verbose_name='IOC Type')),
                ('value', models.TextField(verbose_name='IOC Value')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('enriched', 'Enriched'), ('not_found', 'Not Found')], default='pending', max_length=20, verbose_name='Enrichment Status')),
                ('first_seen', models.DateTimeField(default=django.utils.timezone.now, verbose_name='First Seen')),
                ('last_checked', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Last Checked')),
                ('last_matched', models.DateTimeField(blank=True, null=True, verbose_name='Last Matched')),
                ('source', models.CharField(default='manual', help_text='Original source of the IOC (alert, feed, manual)', max_length=100, verbose_name='Source')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('tlp', models.CharField(choices=[('white', 'TLP:WHITE'), ('green', 'TLP:GREEN'), ('amber', 'TLP:AMBER'), ('red', 'TLP:RED')], default='amber', max_length=10, verbose_name='TLP')),
                ('confidence', models.FloatField(default=0.0, verbose_name='Confidence')),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags associated with this IOC', verbose_name='Tags')),
                ('es_index', models.CharField(blank=True, help_text='Name of the Elasticsearch index where this IOC is stored', max_length=100, verbose_name='Elasticsearch Index')),
                ('es_doc_id', models.CharField(blank=True, help_text='ID of the document in Elasticsearch', max_length=100, verbose_name='Elasticsearch Document ID')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enriched_iocs', to='companies.company', verbose_name='Company')),
            ],
            options={
                'verbose_name': 'Enriched IOC',
                'verbose_name_plural': 'Enriched IOCs',
                'ordering': ['-last_checked'],
                'unique_together': {('company', 'ioc_type', 'value')},
            },
        ),
        migrations.CreateModel(
            name='IOCFeedMatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Match Time')),
                ('feed_confidence', models.FloatField(default=0.0, verbose_name='Feed Confidence')),
                ('feed_tags', models.JSONField(blank=True, default=list, verbose_name='Feed Tags')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata about the match', verbose_name='Metadata')),
                ('feed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ioc_matches', to='sentinelvision.feedmodule', verbose_name='Feed')),
                ('ioc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feed_matches', to='sentinelvision.enrichedioc', verbose_name='IOC')),
            ],
            options={
                'verbose_name': 'IOC-Feed Match',
                'verbose_name_plural': 'IOC-Feed Matches',
                'ordering': ['-match_time'],
                'unique_together': {('ioc', 'feed')},
            },
        ),
        migrations.AddField(
            model_name='enrichedioc',
            name='matched_feeds',
            field=models.ManyToManyField(related_name='matched_iocs', through='sentinelvision.IOCFeedMatch', to='sentinelvision.feedmodule', verbose_name='Matched Feeds'),
        ),
        migrations.AddIndex(
            model_name='iocfeedmatch',
            index=models.Index(fields=['ioc', 'feed'], name='sentinelvis_ioc_id_56b0ee_idx'),
        ),
        migrations.AddIndex(
            model_name='iocfeedmatch',
            index=models.Index(fields=['match_time'], name='sentinelvis_match_t_e66f60_idx'),
        ),
        migrations.AddIndex(
            model_name='enrichedioc',
            index=models.Index(fields=['company', 'ioc_type'], name='sentinelvis_company_01c5c8_idx'),
        ),
        migrations.AddIndex(
            model_name='enrichedioc',
            index=models.Index(fields=['company', 'status'], name='sentinelvis_company_1a7df0_idx'),
        ),
        migrations.AddIndex(
            model_name='enrichedioc',
            index=models.Index(fields=['value'], name='sentinelvis_value_ad7b96_idx'),
        ),
        migrations.AddIndex(
            model_name='enrichedioc',
            index=models.Index(fields=['last_checked'], name='sentinelvis_last_ch_69b056_idx'),
        ),
        migrations.AddIndex(
            model_name='enrichedioc',
            index=models.Index(fields=['status', 'last_checked'], name='sentinelvis_status_76a25e_idx'),
        ),
    ] 