
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_sessionannotation_frame_step'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('key_binding', models.CharField(blank=True, max_length=1)),
                ('color', models.CharField(default='#9333ea', max_length=7)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='tracker.project')),
            ],
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.CreateModel(
            name='IndependentVariableDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=120)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('value_type', models.CharField(choices=[('text', 'Texte'), ('numeric', 'Numérique'), ('set', 'Valeur dans une liste'), ('timestamp', 'Horodatage')], default='text', max_length=20)),
                ('set_values', models.TextField(blank=True, help_text='Valeurs séparées par des virgules')),
                ('default_value', models.CharField(blank=True, max_length=255)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variable_definitions', to='tracker.project')),
            ],
            options={'ordering': ['sort_order', 'label']},
        ),
        migrations.CreateModel(
            name='ObservationVariableValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(blank=True, max_length=255)),
                ('definition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='tracker.independentvariabledefinition')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variable_values', to='tracker.observationsession')),
            ],
            options={'ordering': ['definition__sort_order', 'definition__label']},
        ),
        migrations.AddField(
            model_name='observationsession',
            name='session_kind',
            field=models.CharField(choices=[('media', 'Média'), ('live', 'Live')], default='media', max_length=10),
        ),
        migrations.AddField(
            model_name='observationsession',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='observationsession',
            name='recorded_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='observationsession',
            name='video',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='tracker.videoasset'),
        ),
        migrations.AddField(
            model_name='observationevent',
            name='frame_index',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='observationevent',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='tracker.subject'),
        ),
        migrations.AddConstraint(
            model_name='subject',
            constraint=models.UniqueConstraint(fields=('project', 'name'), name='unique_subject_name_per_project'),
        ),
        migrations.AddConstraint(
            model_name='independentvariabledefinition',
            constraint=models.UniqueConstraint(fields=('project', 'label'), name='unique_variable_label_per_project'),
        ),
        migrations.AddConstraint(
            model_name='observationvariablevalue',
            constraint=models.UniqueConstraint(fields=('session', 'definition'), name='unique_variable_value_per_session'),
        ),
    ]
