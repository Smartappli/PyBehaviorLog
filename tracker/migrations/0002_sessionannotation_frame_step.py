from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='observationsession',
            name='frame_step_seconds',
            field=models.DecimalField(
                decimal_places=4,
                default=0.04,
                max_digits=7,
                validators=[
                    django.core.validators.MinValueValidator(0.001),
                    django.core.validators.MaxValueValidator(1.0),
                ],
            ),
        ),
        migrations.CreateModel(
            name='SessionAnnotation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp_seconds', models.DecimalField(decimal_places=3, max_digits=10)),
                ('title', models.CharField(max_length=120)),
                ('note', models.TextField(blank=True)),
                ('color', models.CharField(default='#f59e0b', max_length=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cowlog_annotations', to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='tracker.observationsession')),
            ],
            options={
                'ordering': ['timestamp_seconds', 'pk'],
            },
        ),
    ]
