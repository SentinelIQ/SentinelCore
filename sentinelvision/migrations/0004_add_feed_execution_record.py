from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('sentinelvision', '0002_analyzermodule_cron_schedule_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedExecutionRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('source', models.CharField(choices=[('manual', 'Manual Execution'), ('scheduled', 'Scheduled Execution')], default='manual', max_length=20, verbose_name='Execution Source')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')], default='pending', max_length=20, verbose_name='Execution Status')),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Started At')),
                ('ended_at', models.DateTimeField(blank=True, null=True, verbose_name='Ended At')),
                ('log', models.TextField(blank=True, help_text='Detailed log of the execution process', verbose_name='Execution Log')),
                ('iocs_processed', models.PositiveIntegerField(default=0, help_text='Number of IOCs processed during execution', verbose_name='IOCs Processed')),
                ('error_message', models.TextField(blank=True, help_text='Error message if execution failed', verbose_name='Error Message')),
                ('executed_by', models.ForeignKey(blank=True, help_text='User who triggered the execution (null if automated)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feed_executions', to='auth.user', verbose_name='Executed By')),
                ('feed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='execution_records', to='sentinelvision.feedmodule', verbose_name='Feed Module')),
            ],
            options={
                'verbose_name': 'Feed Execution Record',
                'verbose_name_plural': 'Feed Execution Records',
                'ordering': ['-started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='feedexecutionrecord',
            index=models.Index(fields=['feed', '-started_at'], name='sentinelvis_feed_id_6f1fee_idx'),
        ),
        migrations.AddIndex(
            model_name='feedexecutionrecord',
            index=models.Index(fields=['status'], name='sentinelvis_status_e0dcec_idx'),
        ),
        migrations.AddIndex(
            model_name='feedexecutionrecord',
            index=models.Index(fields=['source'], name='sentinelvis_source_4b3aa8_idx'),
        ),
    ] 