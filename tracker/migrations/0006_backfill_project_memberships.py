from django.db import migrations


def forwards(apps, schema_editor):
    project_model = apps.get_model('tracker', 'Project')
    membership_model = apps.get_model('tracker', 'ProjectMembership')

    through = project_model.collaborators.through
    existing = set(membership_model.objects.values_list('project_id', 'user_id'))

    memberships = []
    for project in project_model.objects.all().iterator():
        owner_key = (project.id, project.owner_id)
        if owner_key not in existing:
            memberships.append(
                membership_model(
                    project_id=project.id,
                    user_id=project.owner_id,
                    role='owner',
                )
            )
            existing.add(owner_key)

    membership_model.objects.bulk_create(memberships, ignore_conflicts=True)

    editor_memberships = []
    collaborator_rows = through.objects.all().values_list('project_id', 'user_id')
    for project_id, user_id in collaborator_rows.iterator():
        key = (project_id, user_id)
        if key not in existing:
            editor_memberships.append(
                membership_model(
                    project_id=project_id,
                    user_id=user_id,
                    role='editor',
                )
            )
            existing.add(key)

    membership_model.objects.bulk_create(editor_memberships, ignore_conflicts=True)


def backwards(apps, schema_editor):
    membership_model = apps.get_model('tracker', 'ProjectMembership')
    membership_model.objects.filter(role__in=['owner', 'editor']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('tracker', '0005_keyboardprofile_observationsession_keyboard_profile_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
