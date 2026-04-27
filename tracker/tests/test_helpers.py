from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from tracker.models import (
    Behavior,
    IndependentVariableDefinition,
    KeyboardProfile,
    Modifier,
    ObservationEvent,
    ObservationSession,
    ObservationTemplate,
    ObservationVariableValue,
    Project,
    SessionVideoLink,
    Subject,
    SubjectGroup,
    VideoAsset,
)
from tracker.views import (
    build_agreement_analysis,
    build_boris_like_payload,
    build_ethogram_payload,
    build_integrity_report,
    build_keyboard_profile_payload,
    build_media_analysis,
    build_project_boris_payload,
    build_project_statistics,
    build_reproducibility_bundle,
    build_statistics,
    build_subject_statistics,
    build_transition_rows,
    import_ethogram_payload,
    import_project_payload,
    import_session_payload,
    parse_tabular_session_rows,
    resolve_event_kind,
)

User = get_user_model()


class HelperTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='olivier', password='pass12345')
        self.project = Project.objects.create(owner=self.user, name='Project 1')
        self.point_behavior = Behavior.objects.create(
            project=self.project, name='Eat', key_binding='e'
        )
        self.state_behavior = Behavior.objects.create(
            project=self.project,
            name='Stand',
            key_binding='s',
            mode=Behavior.MODE_STATE,
        )
        self.modifier = Modifier.objects.create(project=self.project, name='Near', key_binding='n')
        self.subject = Subject.objects.create(project=self.project, name='Cow 1', key_binding='c')
        self.session = ObservationSession.objects.create(
            project=self.project,
            observer=self.user,
            title='Live session',
            session_kind='live',
        )

    def test_resolve_event_kind_for_state(self):
        kind1 = resolve_event_kind(self.session, self.state_behavior, None)
        self.assertEqual(kind1, ObservationEvent.KIND_START)
        ObservationEvent.objects.create(
            session=self.session,
            behavior=self.state_behavior,
            event_kind=ObservationEvent.KIND_START,
            timestamp_seconds=Decimal('1.000'),
        )
        kind2 = resolve_event_kind(self.session, self.state_behavior, None)
        self.assertEqual(kind2, ObservationEvent.KIND_STOP)

    def test_build_statistics_subjects_transitions_and_integrity(self):
        event1 = ObservationEvent.objects.create(
            session=self.session,
            behavior=self.point_behavior,
            subject=self.subject,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.000'),
        )
        event1.subjects.add(self.subject)
        start_event = ObservationEvent.objects.create(
            session=self.session,
            behavior=self.state_behavior,
            subject=self.subject,
            event_kind=ObservationEvent.KIND_START,
            timestamp_seconds=Decimal('2.000'),
        )
        start_event.subjects.add(self.subject)
        stop_event = ObservationEvent.objects.create(
            session=self.session,
            behavior=self.state_behavior,
            subject=self.subject,
            event_kind=ObservationEvent.KIND_STOP,
            timestamp_seconds=Decimal('5.000'),
        )
        stop_event.subjects.add(self.subject)
        stats = build_statistics(self.session)
        subject_rows = build_subject_statistics(self.session)
        transitions = build_transition_rows(self.session)
        integrity = build_integrity_report(self.session)
        self.assertEqual(stats['session_event_count'], 3)
        self.assertEqual(subject_rows[0]['subject'], 'Cow 1')
        self.assertEqual(sum(row['count'] for row in transitions), 2)
        self.assertEqual(integrity['issue_count'], 0)

    def test_build_project_statistics_and_payloads(self):
        payload = build_ethogram_payload(self.project)
        self.assertEqual(payload['schema'], 'pybehaviorlog-0.9.5-ethogram')
        imported_categories, _, imported_behaviors = import_ethogram_payload(
            self.project, payload, replace_existing=False
        )
        self.assertEqual(imported_categories, 0)
        self.assertEqual(imported_behaviors, 0)
        ObservationEvent.objects.create(
            session=self.session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.000'),
        )
        analytics = build_project_statistics(self.project)
        boris_payload = build_boris_like_payload(self.session)
        project_payload = build_project_boris_payload(self.project)
        self.assertEqual(analytics['session_count'], 1)
        self.assertEqual(analytics['event_count'], 1)
        self.assertEqual(boris_payload['schema'], 'boris-observation-v3')
        self.assertEqual(project_payload['schema'], 'boris-project-v3')

    def test_import_session_payload_v83(self):
        payload = {
            'schema': 'pybehaviorlog-0.9.5-session',
            'workflow_status': 'validated',
            'review_notes': 'Checked',
            'events': [
                {
                    'behavior': 'Eat',
                    'event_kind': 'point',
                    'timestamp_seconds': 1.5,
                    'subjects': ['Cow 1'],
                    'modifiers': ['Near'],
                    'comment': 'Imported',
                }
            ],
            'annotations': [
                {
                    'timestamp_seconds': 2.0,
                    'title': 'Mark',
                    'note': 'Imported note',
                    'color': '#ff0000',
                }
            ],
        }
        event_count, annotation_count = import_session_payload(
            self.session, payload, clear_existing=True
        )
        self.assertEqual(event_count, 1)
        self.assertEqual(annotation_count, 1)
        event = self.session.events.get()
        self.assertEqual(event.subjects_display, 'Cow 1')
        self.assertEqual(self.session.workflow_status, 'validated')

    def test_import_session_payload_accepts_newer_cowlog_schema(self):
        payload = {
            'schema': 'cowlog-results-v2',
            'events': [{'behavior': 'Eat', 'event_kind': 'point', 'time': 1.5}],
            'annotations': [],
        }
        event_count, annotation_count = import_session_payload(
            self.session, payload, clear_existing=True
        )
        self.assertEqual(event_count, 1)
        self.assertEqual(annotation_count, 0)

    def test_import_session_payload_applies_cowlog_metadata_to_notes(self):
        payload = {
            'schema': 'cowlog-results-v2',
            'metadata': {
                'session': 'Imported header session',
                'project': 'Imported header project',
                'primary_video': 'clip.mp4',
            },
            'events': [{'behavior': 'Eat', 'event_kind': 'point', 'time': 1.5}],
            'annotations': [],
        }
        import_session_payload(self.session, payload, clear_existing=True)
        import_session_payload(self.session, payload, clear_existing=True)
        self.session.refresh_from_db()
        self.assertIn('Imported CowLog metadata:', self.session.notes)
        self.assertIn('session: Imported header session', self.session.notes)
        self.assertIn('project: Imported header project', self.session.notes)
        self.assertIn('primary_video: clip.mp4', self.session.notes)
        self.assertEqual(self.session.notes.count('Imported CowLog metadata:'), 1)

    def test_import_session_payload_accepts_mapping_event_rows(self):
        payload = {
            'schema': 'boris-observation-v4',
            'events': {
                'evt-1': {'behavior': 'Eat', 'event_kind': 'point', 'time': 1.5},
                'evt-2': {'behavior': 'Stand', 'event_kind': 'start', 'time': 2.0},
            },
            'annotations': {
                'ann-1': {'time': 2.2, 'title': 'Marker', 'note': 'mapping annotation'},
            },
            'segments': {
                'seg-1': {'title': 'Segment 1', 'start_seconds': 0.0, 'end_seconds': 3.0},
            },
        }
        event_count, annotation_count = import_session_payload(
            self.session, payload, clear_existing=True
        )
        self.assertEqual(event_count, 2)
        self.assertEqual(annotation_count, 1)
        self.assertEqual(self.session.events.count(), 2)
        self.assertEqual(self.session.annotations.count(), 1)

    def test_import_session_payload_merges_multiple_boris_observations(self):
        definition = IndependentVariableDefinition.objects.create(
            project=self.project,
            label='Temperature',
            value_type=IndependentVariableDefinition.TYPE_NUMERIC,
        )
        payload = {
            'schema': 'boris-observation-v4',
            'observations': [
                {
                    'title': 'Obs A',
                    'media_paths': ['videos/a.mp4'],
                    'events': [{'behavior': 'Eat', 'event_kind': 'point', 'time': 1.0}],
                    'annotations': [{'time': 1.2, 'title': 'A', 'note': 'first'}],
                    'variables': {'Temperature': '18'},
                },
                {
                    'title': 'Obs B',
                    'media_paths': ['videos/b.mp4'],
                    'events': [{'behavior': 'Stand', 'event_kind': 'start', 'time': 2.0}],
                    'annotations': [{'time': 2.4, 'title': 'B', 'note': 'second'}],
                    'independent_variables': {'Temperature': '19'},
                },
            ],
        }
        event_count, annotation_count = import_session_payload(
            self.session, payload, clear_existing=True
        )
        self.assertEqual(event_count, 2)
        self.assertEqual(annotation_count, 2)
        import_session_payload(self.session, payload, clear_existing=True)
        self.assertTrue(self.session.events.filter(comment__contains='BORIS observation').exists())
        self.assertTrue(self.session.annotations.filter(title__startswith='[Obs').exists())
        self.session.refresh_from_db()
        self.assertIn('Imported BORIS observations: Obs A, Obs B', self.session.notes)
        self.assertIn('Imported BORIS media labels: videos/a.mp4, videos/b.mp4', self.session.notes)
        self.assertEqual(self.session.notes.count('Imported BORIS observations:'), 1)
        self.assertEqual(self.session.notes.count('Imported BORIS media labels:'), 1)
        stored_value = ObservationVariableValue.objects.get(
            session=self.session, definition=definition
        )
        self.assertEqual(stored_value.value, '19')

    def test_keyboard_profile_payload_and_reproducibility_bundle(self):
        profile = KeyboardProfile.objects.create(
            project=self.project,
            name='Default',
            is_default=True,
            behavior_bindings={str(self.point_behavior.pk): 'x'},
            modifier_bindings={str(self.modifier.pk): 'm'},
            subject_bindings={str(self.subject.pk): 'z'},
        )
        payload = build_keyboard_profile_payload(self.project)
        bundle = build_reproducibility_bundle(self.project)
        self.assertIn('ethogram.json', bundle)
        self.assertIn('manifest.json', bundle)
        self.assertIn('compatibility_report.json', bundle)
        self.assertIn(str(self.point_behavior.pk), payload['behavior_bindings'])
        self.assertTrue(profile.is_default)

    def test_agreement_analysis(self):
        other_session = ObservationSession.objects.create(
            project=self.project,
            observer=self.user,
            title='Second session',
            session_kind='live',
        )
        ObservationEvent.objects.create(
            session=self.session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.000'),
        )
        ObservationEvent.objects.create(
            session=other_session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.000'),
        )
        agreement = build_agreement_analysis(self.session, other_session)
        self.assertEqual(agreement['percent_agreement'], 100.0)
        self.assertGreaterEqual(agreement['bucket_count'], 1)

    def test_media_analysis_and_relative_paths(self):
        video = VideoAsset.objects.create(
            project=self.project,
            title='clip.wav',
            file=SimpleUploadedFile('clip.wav', b'RIFF\x24\x00\x00\x00WAVEfmt '),
        )
        self.session.video = video
        self.session.save(update_fields=['video'])
        SessionVideoLink.objects.create(session=self.session, video=video, sort_order=0)
        boris_payload = build_boris_like_payload(self.session)
        media = build_media_analysis(self.session)
        self.assertTrue(
            boris_payload['observations'][0]['media_paths'][0].startswith('videos/clip')
        )
        self.assertTrue(boris_payload['observations'][0]['media_paths'][0].endswith('.wav'))
        self.assertTrue(media[0]['relative_path'].startswith('videos/clip'))
        self.assertTrue(media[0]['relative_path'].endswith('.wav'))

    def test_parse_tabular_session_rows(self):
        rows = [
            {
                'time': '1.250',
                'behavior': 'Eat',
                'event_kind': 'point',
                'subjects': 'Cow 1',
                'modifiers': 'Near',
                'comment': 'Imported from CSV',
            }
        ]
        payload, report = parse_tabular_session_rows(
            self.session,
            rows,
            source_format='boris-tabular-csv-v1',
        )
        self.assertEqual(report['event_count'], 1)
        self.assertEqual(payload['schema'], 'boris-tabular-csv-v1')
        self.assertEqual(payload['events'][0]['behavior'], 'Eat')

    def test_import_project_payload_with_templates_and_sessions(self):
        payload = {
            'schema': 'boris-project-v3',
            'ethogram': build_ethogram_payload(self.project),
            'subject_groups': [
                {
                    'name': 'Adults',
                    'description': 'Adult cattle',
                    'color': '#123456',
                    'sort_order': 1,
                }
            ],
            'subjects': [
                {
                    'name': 'Cow 2',
                    'description': 'Imported subject',
                    'key_binding': 'v',
                    'color': '#654321',
                    'sort_order': 2,
                    'groups': ['Adults'],
                }
            ],
            'variables': [
                {
                    'label': 'Temperature',
                    'description': 'Ambient',
                    'value_type': 'numeric',
                    'set_values': [],
                    'default_value': '12',
                    'sort_order': 1,
                }
            ],
            'observation_templates': [
                {
                    'name': 'Imported template',
                    'description': 'A template',
                    'default_session_kind': 'live',
                    'behaviors': ['Eat'],
                    'modifiers': ['Near'],
                    'subjects': ['Cow 1', 'Cow 2'],
                    'variable_definitions': ['Temperature'],
                }
            ],
            'sessions': [
                {
                    'schema': 'boris-observation-v3',
                    'workflow_status': 'draft',
                    'review_notes': 'Imported via project helper',
                    'variables': {'Temperature': '17'},
                    'observations': [
                        {
                            'title': 'Imported BORIS session',
                            'primary_video': 'No file yet',
                            'synced_videos': ['No file yet'],
                            'events': [
                                {
                                    'behavior': 'Eat',
                                    'event_kind': 'point',
                                    'time': 1.25,
                                    'subjects': ['Cow 2'],
                                    'modifiers': ['Near'],
                                    'comment': 'Imported event',
                                }
                            ],
                            'annotations': [
                                {
                                    'time': 2.0,
                                    'title': 'Marker',
                                    'note': 'Imported annotation',
                                    'color': '#ff0000',
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        summary = import_project_payload(self.project, payload, actor=self.user)
        self.assertEqual(summary['templates_created'], 1)
        self.assertEqual(summary['sessions_imported'], 1)
        self.assertTrue(SubjectGroup.objects.filter(project=self.project, name='Adults').exists())
        self.assertTrue(
            ObservationTemplate.objects.filter(
                project=self.project, name='Imported template'
            ).exists()
        )
        imported_session = ObservationSession.objects.get(
            project=self.project, title='Imported BORIS session'
        )
        self.assertEqual(imported_session.events.count(), 1)
        self.assertEqual(imported_session.annotations.count(), 1)

    def test_import_project_payload_accepts_newer_boris_schema(self):
        payload = {
            'schema': 'boris-project-v4',
            'ethogram': build_ethogram_payload(self.project),
            'sessions': [],
        }
        summary = import_project_payload(
            self.project, payload, actor=self.user, import_sessions=False
        )
        self.assertIn('categories_created', summary)

    def test_import_ethogram_payload_accepts_newer_boris_observation_schema(self):
        payload = {
            'schema': 'boris-observation-v4',
            'categories': [{'name': 'Core', 'color': '#222222', 'sort_order': 1}],
            'behaviors': [{'name': 'Graze', 'key_binding': 'g', 'mode': Behavior.MODE_POINT}],
        }
        categories, modifiers, behaviors = import_ethogram_payload(
            self.project, payload, replace_existing=False
        )
        self.assertEqual(categories, 1)
        self.assertEqual(modifiers, 0)
        self.assertEqual(behaviors, 1)
