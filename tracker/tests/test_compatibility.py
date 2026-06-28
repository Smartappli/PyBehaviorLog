import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from tracker.models import (
    Behavior,
    IndependentVariableDefinition,
    Modifier,
    ObservationEvent,
    ObservationSession,
    ObservationVariableValue,
    Project,
    SessionAnnotation,
    SessionVideoLink,
    Subject,
    VideoAsset,
)
from tracker.views import (
    build_behavioral_sequences_text,
    build_binary_table_rows,
    build_boris_aggregated_event_rows,
    build_boris_tabular_event_rows,
    build_feral_payload,
    build_native_boris_project_payload,
    build_project_compatibility_report,
    build_session_compatibility_report,
    build_textgrid_text,
    import_project_payload,
    load_session_import_payload,
    normalize_native_boris_project_payload,
    parse_cowlog_results_text,
    parse_tabular_session_rows,
)

User = get_user_model()


class CompatibilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='olivier')
        self.client = Client()
        self.client.force_login(self.user)
        self.project = Project.objects.create(owner=self.user, name='Project 1')
        self.point_behavior = Behavior.objects.create(
            project=self.project,
            name='Eat',
            key_binding='E',
        )
        self.state_behavior = Behavior.objects.create(
            project=self.project,
            name='Stand',
            key_binding='S',
            mode=Behavior.MODE_STATE,
        )
        self.modifier = Modifier.objects.create(project=self.project, name='Near', key_binding='N')
        self.subject = Subject.objects.create(project=self.project, name='Cow 1', key_binding='C')
        self.session = ObservationSession.objects.create(
            project=self.project,
            observer=self.user,
            title='Session 1',
            session_kind='live',
        )

    def test_load_session_import_payload_supports_cowlog_text(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'1.0\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(report['source_hint'], 'cowlog_text_time_token')
        self.assertEqual(payload['events'][0]['behavior'], 'Eat')
        self.assertEqual(payload['events'][0]['modifiers'], ['Near'])

    def test_parse_cowlog_results_text_strict_mode_rejects_unknown_behavior(self):
        with self.assertRaises(ValueError):
            parse_cowlog_results_text(self.session, '1.0\tUnknownBehavior\tNear\n', strict=True)

    def test_load_session_import_payload_supports_cowlog_timecodes(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'00:01:02.500\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(payload['events'][0]['time'], 62.5)

    def test_load_session_import_payload_supports_cowlog_iso8601_durations(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'PT1M2.5S\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(payload['events'][0]['time'], 62.5)

    def test_load_session_import_payload_supports_cowlog_frame_timecodes(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'00:00:10:12\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertAlmostEqual(payload['events'][0]['time'], 10.48, places=3)

    def test_load_session_import_payload_supports_smpte_semicolon_timecodes(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'00:00:10;12\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertAlmostEqual(payload['events'][0]['time'], 10.48, places=3)

    def test_load_session_import_payload_supports_cowlog_frame_rate_metadata(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'# fps\t30\n00:00:10:15\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(report['frame_rate'], '30')
        self.assertAlmostEqual(payload['events'][0]['time'], 10.5, places=3)

    def test_load_session_import_payload_supports_cowlog_frame_rate_with_unit(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'# fps\t29.97 fps\n00:00:10:15\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(report['frame_rate'], '29.97 fps')
        self.assertAlmostEqual(payload['events'][0]['time'], 10.5005, places=3)

    def test_load_session_import_payload_supports_cowlog_frame_rate_ratio(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'# fps\t30000/1001\n00:00:10:15\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(report['frame_rate'], '30000/1001')
        self.assertAlmostEqual(payload['events'][0]['time'], 10.5005, places=3)

    def test_load_session_import_payload_supports_cowlog_colon_metadata(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'# fps:30\n00:00:10:15\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(report['frame_rate'], '30')
        self.assertAlmostEqual(payload['events'][0]['time'], 10.5, places=3)

    def test_load_session_import_payload_supports_cowlog_state_aliases(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'2.0\tStand\tbegin\tCow 1\n4.0\tStand\tend\tCow 1\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(payload['events'][0]['event_kind'], ObservationEvent.KIND_START)
        self.assertEqual(payload['events'][1]['event_kind'], ObservationEvent.KIND_STOP)

    def test_load_session_import_payload_supports_symbolic_state_aliases(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'2.0\tStand\t+\tCow 1\n4.0\tStand\t-\tCow 1\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(payload['events'][0]['event_kind'], ObservationEvent.KIND_START)
        self.assertEqual(payload['events'][1]['event_kind'], ObservationEvent.KIND_STOP)

    def test_load_session_import_payload_supports_semicolon_cowlog_rows(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'2.0;Stand;begin;Cow 1\n4.0;Stand;end;Cow 1\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(payload['events'][0]['event_kind'], ObservationEvent.KIND_START)
        self.assertEqual(payload['events'][1]['event_kind'], ObservationEvent.KIND_STOP)

    def test_load_session_import_payload_parses_cowlog_metadata_annotations(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'# annotation\t3.0\tMarker\tInteresting moment\n1.0\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(report['annotation_count'], 1)
        self.assertEqual(payload['annotations'][0]['title'], 'Marker')
        self.assertEqual(payload['annotations'][0]['note'], 'Interesting moment')

    def test_load_session_import_payload_parses_quoted_cowlog_metadata_annotations(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'# annotation 3.0 Marker "Interesting moment with spaces"\n1.0\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(report['annotation_count'], 1)
        self.assertEqual(payload['annotations'][0]['title'], 'Marker')
        self.assertEqual(payload['annotations'][0]['note'], 'Interesting moment with spaces')

    def test_load_session_import_payload_parses_cowlog_headers(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'# session\tHeader Session\n# project\tHeader Project\n# primary_video\tclip.mp4\n1.0\tEat\tNear\n',
            content_type='text/plain',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'cowlog-results-v1')
        self.assertEqual(payload['metadata']['session'], 'Header Session')
        self.assertEqual(payload['metadata']['project'], 'Header Project')
        self.assertEqual(payload['metadata']['primary_video'], 'clip.mp4')

    def test_session_import_view_accepts_cowlog_text(self):
        upload = SimpleUploadedFile(
            'cowlog.txt',
            b'1.0\tEat\tNear\n',
            content_type='text/plain',
        )
        response = self.client.post(
            reverse('tracker:session_import_json', args=[self.session.pk]),
            data={'file': upload, 'clear_existing': 'on'},
        )
        self.assertEqual(response.status_code, 302)
        event = self.session.events.get()
        self.assertEqual(event.behavior.name, 'Eat')
        self.assertEqual(event.modifiers_display, 'Near')

    def test_load_session_import_payload_supports_state_intervals_from_tabular_rows(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time,stop,behavior,subject,modifier,comment\n1.0,3.0,Stand,Cow 1,Near,Frame A\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertEqual(report['source_hint'], 'tabular_header_delimiter')
        self.assertEqual(len(payload['events']), 2)
        self.assertEqual(payload['events'][0]['event_kind'], 'start')
        self.assertEqual(payload['events'][1]['event_kind'], 'stop')

    def test_parse_tabular_session_rows_strict_mode_rejects_unknown_behavior(self):
        with self.assertRaises(ValueError):
            parse_tabular_session_rows(
                self.session,
                [{'time': '1.0', 'behavior': 'UnknownBehavior'}],
                source_format='boris-tabular-csv-v1',
                strict=True,
            )

    def test_load_session_import_payload_supports_tabular_timecodes(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time,stop,behavior\n00:00:05.100,00:00:08.600,Stand\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertEqual(payload['events'][0]['time'], 5.1)
        self.assertEqual(payload['events'][1]['time'], 8.6)

    def test_load_session_import_payload_supports_tabular_iso8601_durations(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time,stop,behavior\nPT5S,PT8.5S,Stand\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertEqual(payload['events'][0]['time'], 5.0)
        self.assertEqual(payload['events'][1]['time'], 8.5)

    def test_load_session_import_payload_supports_semicolon_csv_with_comma_decimals(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time;stop;behavior\n00:00:05,100;00:00:08,600;Stand\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertAlmostEqual(payload['events'][0]['time'], 5.1, places=3)
        self.assertAlmostEqual(payload['events'][1]['time'], 8.6, places=3)

    def test_load_session_import_payload_supports_tabular_frame_timecodes(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time,stop,behavior\n00:00:05:10,00:00:08:20,Stand\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertAlmostEqual(payload['events'][0]['time'], 5.4, places=3)
        self.assertAlmostEqual(payload['events'][1]['time'], 8.8, places=3)

    def test_load_session_import_payload_supports_tabular_smpte_semicolon_timecodes(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time,stop,behavior\n00:00:05;10,00:00:08;20,Stand\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertAlmostEqual(payload['events'][0]['time'], 5.4, places=3)
        self.assertAlmostEqual(payload['events'][1]['time'], 8.8, places=3)

    def test_load_session_import_payload_supports_tabular_custom_frame_rate(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time,stop,behavior,frame_rate\n00:00:05:10,00:00:08:20,Stand,50 fps\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertAlmostEqual(payload['events'][0]['time'], 5.2, places=3)
        self.assertAlmostEqual(payload['events'][1]['time'], 8.4, places=3)

    def test_load_session_import_payload_supports_tabular_ratio_frame_rate(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time,stop,behavior,frame_rate\n00:00:05:10,00:00:08:20,Stand,30000/1001\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertAlmostEqual(payload['events'][0]['time'], 5.3336, places=3)
        self.assertAlmostEqual(payload['events'][1]['time'], 8.6673, places=3)

    def test_load_session_import_payload_supports_state_duration_column(self):
        upload = SimpleUploadedFile(
            'boris_rows.csv',
            b'time,duration,behavior\n10.0,2.5,Stand\n',
            content_type='text/csv',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-csv-v1')
        self.assertEqual(payload['events'][0]['event_kind'], ObservationEvent.KIND_START)
        self.assertEqual(payload['events'][1]['event_kind'], ObservationEvent.KIND_STOP)
        self.assertEqual(payload['events'][1]['time'], 12.5)

    def test_load_session_import_payload_supports_boris_tabular_preamble(self):
        upload = SimpleUploadedFile(
            'boris_export.tsv',
            (
                b'Observation id\tObservation 1\n\n'
                b'Media file(s)\n\n'
                b'Time\tMedia file path\tTotal length\tFPS\tSubject\tBehavior\t'
                b'Behavioral category\tComment\tStatus\n'
                b'1.000\tclip.mp4\t10.000\t2.0\tCow 1\tStand\t\tbegin\tSTART\n'
                b'3.000\tclip.mp4\t10.000\t2.0\tCow 1\tStand\t\tend\tSTOP\n'
            ),
            content_type='text/tab-separated-values',
        )
        payload, report = load_session_import_payload(upload, self.session)
        self.assertEqual(report['detected_format'], 'boris-tabular-tsv-v1')
        self.assertEqual(len(payload['events']), 2)
        self.assertEqual(payload['events'][0]['event_kind'], ObservationEvent.KIND_START)
        self.assertEqual(payload['events'][1]['event_kind'], ObservationEvent.KIND_STOP)
        self.assertEqual(payload['events'][0]['subjects'], ['Cow 1'])

    def test_native_boris_project_payload_imports_ethogram_media_and_events(self):
        target_project = Project.objects.create(owner=self.user, name='Native BORIS target')
        native_payload = {
            'project_name': 'Native BORIS source',
            'project_description': 'Native project shape',
            'project_format_version': '7.0',
            'behavioral_categories': ['Activity'],
            'behavioral_categories_config': {
                '0': {'name': 'Activity', 'color': '#123456'},
            },
            'subjects_conf': {
                '0': {'key': '1', 'name': 'Subject A', 'description': 'Focal subject'}
            },
            'independent_variables': {
                '0': {
                    'label': 'Location',
                    'description': 'Observation site',
                    'type': 'text',
                    'default value': '',
                    'possible values': '',
                }
            },
            'behaviors_conf': {
                '0': {
                    'type': 'Point event',
                    'key': 'p',
                    'code': 'Peck',
                    'description': 'Pecking',
                    'category': 'Activity',
                    'modifiers': {
                        '0': {
                            'name': 'speed',
                            'type': 0,
                            'values': ['fast (f)', 'slow'],
                        }
                    },
                },
                '1': {
                    'type': 'State event',
                    'key': 'r',
                    'code': 'Rest',
                    'description': 'Resting',
                    'category': 'Activity',
                    'modifiers': {},
                },
            },
            'observations': {
                'Observation 1': {
                    'file': {'1': ['clips/cam1.mp4']},
                    'type': 'MEDIA',
                    'date': '2026-06-26T12:00:00',
                    'description': 'Native observation',
                    'time offset': 0.0,
                    'independent_variables': {'Location': 'Barn'},
                    'media_info': {
                        'length': {'clips/cam1.mp4': 10.0},
                        'fps': {'clips/cam1.mp4': 2.0},
                    },
                    'events': [
                        [1.0, 'Subject A', 'Peck', 'fast', 'visible'],
                        [2.0, 'Subject A', 'Rest', '', ''],
                        [4.0, 'Subject A', 'Rest', '', ''],
                    ],
                }
            },
        }
        normalized = normalize_native_boris_project_payload(native_payload)
        self.assertEqual(normalized['schema'], 'boris-project-v7')
        self.assertEqual(normalized['categories'][0]['color'], '#123456')
        summary = import_project_payload(target_project, native_payload, actor=self.user)
        self.assertEqual(summary['sessions_imported'], 1)
        self.assertEqual(target_project.behaviors.count(), 2)
        self.assertEqual(target_project.categories.get(name='Activity').color, '#123456')
        self.assertEqual(target_project.subjects.get().name, 'Subject A')
        self.assertTrue(VideoAsset.objects.filter(project=target_project, title='cam1.mp4').exists())
        imported_session = target_project.sessions.get(title='Observation 1')
        self.assertEqual(imported_session.session_kind, ObservationSession.KIND_MEDIA)
        self.assertEqual(imported_session.variable_values.get().value, 'Barn')
        imported_events = list(imported_session.events.order_by('timestamp_seconds'))
        self.assertEqual([event.event_kind for event in imported_events], ['point', 'start', 'stop'])
        self.assertEqual(imported_events[0].modifiers.get().name, 'fast')

    def test_native_boris_image_observation_preserves_image_index_and_path(self):
        target_project = Project.objects.create(owner=self.user, name='Native BORIS images')
        native_payload = {
            'project_name': 'Native BORIS image source',
            'project_format_version': '7.0',
            'subjects_conf': {},
            'behaviors_conf': {
                '0': {
                    'type': 'Point event',
                    'key': 'p',
                    'code': 'Peck',
                    'description': '',
                    'category': '',
                    'modifiers': {},
                }
            },
            'observations': {
                'Image observation': {
                    'file': {},
                    'type': 'IMAGES',
                    'date': '2026-06-26T12:00:00',
                    'description': 'Images from one directory',
                    'time offset': 0.0,
                    'directories_list': ['pictures/session1'],
                    'independent_variables': {},
                    'events': [
                        [1.0, '', 'Peck', '', '', 3, 'pictures/session1/img003.jpg'],
                    ],
                }
            },
            'behavioral_categories': [],
            'independent_variables': {},
            'coding_map': {},
            'behaviors_coding_map': [],
            'converters': {},
        }
        normalized = normalize_native_boris_project_payload(native_payload)
        observation = normalized['observations'][0]
        self.assertEqual(observation['media_paths'], ['pictures/session1'])
        self.assertEqual(observation['events'][0]['frame_index'], 3)
        self.assertEqual(observation['events'][0]['image_path'], 'pictures/session1/img003.jpg')

        summary = import_project_payload(target_project, native_payload, actor=self.user)
        self.assertEqual(summary['sessions_imported'], 1)
        imported_session = target_project.sessions.get(title='Image observation')
        imported_event = imported_session.events.get()
        self.assertEqual(imported_event.frame_index, 3)
        self.assertEqual(imported_event.comment, 'pictures/session1/img003.jpg')
        self.assertIn('pictures/session1', imported_session.notes)

    def test_session_undo_and_redo_endpoints_restore_event_state(self):
        response = self.client.post(
            reverse('tracker:event_create_api', args=[self.session.pk]),
            data=json.dumps(
                {
                    'behavior_id': self.point_behavior.pk,
                    'timestamp_seconds': '1.000',
                    'modifier_ids': [self.modifier.pk],
                    'subject_ids': [self.subject.pk],
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.session.events.count(), 1)
        undo_response = self.client.post(
            reverse('tracker:session_undo_api', args=[self.session.pk]),
            data='{}',
            content_type='application/json',
        )
        self.assertEqual(undo_response.status_code, 200)
        self.assertEqual(self.session.events.count(), 0)
        redo_response = self.client.post(
            reverse('tracker:session_redo_api', args=[self.session.pk]),
            data='{}',
            content_type='application/json',
        )
        self.assertEqual(redo_response.status_code, 200)
        self.assertEqual(self.session.events.count(), 1)

    def test_behavioral_sequences_and_textgrid_exports(self):
        point_event = ObservationEvent.objects.create(
            session=self.session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.000'),
        )
        point_event.subjects.add(self.subject)
        start_event = ObservationEvent.objects.create(
            session=self.session,
            behavior=self.state_behavior,
            event_kind=ObservationEvent.KIND_START,
            timestamp_seconds=Decimal('2.000'),
        )
        start_event.subjects.add(self.subject)
        stop_event = ObservationEvent.objects.create(
            session=self.session,
            behavior=self.state_behavior,
            event_kind=ObservationEvent.KIND_STOP,
            timestamp_seconds=Decimal('4.000'),
        )
        stop_event.subjects.add(self.subject)
        sequences = build_behavioral_sequences_text(self.session)
        textgrid = build_textgrid_text(self.session)
        self.assertIn('Cow 1:', sequences)
        self.assertIn('Eat|Stand', sequences)
        self.assertIn('Object class = "TextGrid"', textgrid)
        self.assertIn('class = "TextTier"', textgrid)
        self.assertIn('name = "Cow 1_Eat"', textgrid)
        self.assertIn('name = "Cow 1_Stand"', textgrid)

    def test_binary_table_and_compatibility_report(self):
        ObservationEvent.objects.create(
            session=self.session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.000'),
        )
        ObservationEvent.objects.create(
            session=self.session,
            behavior=self.state_behavior,
            event_kind=ObservationEvent.KIND_START,
            timestamp_seconds=Decimal('2.000'),
        )
        ObservationEvent.objects.create(
            session=self.session,
            behavior=self.state_behavior,
            event_kind=ObservationEvent.KIND_STOP,
            timestamp_seconds=Decimal('4.000'),
        )
        rows = build_binary_table_rows(self.session, step_seconds=1.0)
        self.assertEqual(rows[1][1], 1)
        headers, aggregated_rows = build_boris_aggregated_event_rows(self.session)
        self.assertIn('FPS (frame/s)', headers)
        self.assertIn('Media duration (s)', headers)
        self.assertEqual(len(aggregated_rows), 2)
        feral_payload = build_feral_payload(self.session)
        self.assertIn('class_names', feral_payload)
        report = build_session_compatibility_report(self.session)
        self.assertFalse(report['cowlog']['ready'])
        self.assertTrue(report['cowlog']['warnings'])
        self.assertIn('feral_json', report['boris']['documented_exports'])
        self.assertFalse(report['cowcloud']['ready'])
        self.assertEqual(report['cowcloud']['status'], 'blocked_pending_format_contract')

    def test_native_boris_export_profiles(self):
        video = VideoAsset.objects.create(
            project=self.project,
            title='Clip',
            file='videos/clip.mp4',
        )
        media_session = ObservationSession.objects.create(
            project=self.project,
            observer=self.user,
            title='Media Session',
            session_kind=ObservationSession.KIND_MEDIA,
            video=video,
        )
        event = ObservationEvent.objects.create(
            session=media_session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.250'),
            frame_index=38,
            comment='native export',
        )
        event.subjects.add(self.subject)
        event.modifiers.add(self.modifier)

        payload7 = build_native_boris_project_payload(
            self.project, profile='7', sessions=[media_session]
        )
        payload8 = build_native_boris_project_payload(
            self.project, profile='8', sessions=[media_session]
        )
        payload9 = build_native_boris_project_payload(
            self.project, profile='9', sessions=[media_session]
        )

        for payload in (payload7, payload8, payload9):
            self.assertEqual(payload['project_format_version'], '7.0')
            self.assertIn('subjects_conf', payload)
            self.assertIn('behaviors_conf', payload)
            self.assertIn('observations', payload)
            observation = payload['observations']['Media Session']
            self.assertEqual(observation['type'], 'MEDIA')
            self.assertEqual(observation['file'], {'1': ['videos/clip.mp4']})
            self.assertEqual(observation['events'][0][1], 'Cow 1')
            self.assertEqual(observation['events'][0][2], 'Eat')
            self.assertEqual(observation['events'][0][3], 'Near')

        self.assertNotIn('scan_sampling_time', payload7['observations']['Media Session'])
        self.assertEqual(len(payload7['observations']['Media Session']['events'][0]), 5)
        self.assertIn('scan_sampling_time', payload8['observations']['Media Session'])
        self.assertNotIn('visualize_waveform', payload8['observations']['Media Session'])
        self.assertEqual(payload8['observations']['Media Session']['events'][0][5], 38)
        self.assertIn('visualize_waveform', payload9['observations']['Media Session'])
        self.assertIn('behavioral_categories_config', payload9)
        normalized = normalize_native_boris_project_payload(payload9)
        self.assertEqual(normalized['observations'][0]['events'][0]['frame_index'], 38)

    def test_boris_tabular_event_export_rows(self):
        video = VideoAsset.objects.create(
            project=self.project,
            title='Clip',
            file='videos/clip.mp4',
        )
        media_session = ObservationSession.objects.create(
            project=self.project,
            observer=self.user,
            title='Media Session',
            session_kind=ObservationSession.KIND_MEDIA,
            video=video,
        )
        fps_definition = IndependentVariableDefinition.objects.create(
            project=self.project,
            label='fps',
            value_type=IndependentVariableDefinition.TYPE_NUMERIC,
        )
        ObservationVariableValue.objects.create(
            session=media_session,
            definition=fps_definition,
            value='30',
        )
        point_event = ObservationEvent.objects.create(
            session=media_session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.250'),
            frame_index=38,
            comment='tabular point',
        )
        point_event.subjects.add(self.subject)
        point_event.modifiers.add(self.modifier)
        ObservationEvent.objects.create(
            session=media_session,
            behavior=self.state_behavior,
            event_kind=ObservationEvent.KIND_START,
            timestamp_seconds=Decimal('2.000'),
        )
        ObservationEvent.objects.create(
            session=media_session,
            behavior=self.state_behavior,
            event_kind=ObservationEvent.KIND_STOP,
            timestamp_seconds=Decimal('3.000'),
        )

        headers, rows = build_boris_tabular_event_rows(media_session)
        self.assertIn('Observation id', headers)
        self.assertIn('Media duration (s)', headers)
        self.assertIn('FPS', headers)
        self.assertIn('Modifier #1', headers)
        self.assertIn('Behavior type', headers)
        self.assertEqual(len(rows), 3)
        status_index = headers.index('Behavior type')
        frame_index = headers.index('Image index')
        fps_index = headers.index('FPS')
        media_index = headers.index('Media file name')
        self.assertEqual([row[status_index] for row in rows], ['POINT', 'START', 'STOP'])
        self.assertEqual(rows[0][frame_index], 38)
        self.assertEqual(rows[0][fps_index], '30.000')
        self.assertEqual(rows[0][media_index], 'videos/clip.mp4')

    def test_export_endpoints_for_compatibility_formats(self):
        ObservationEvent.objects.create(
            session=self.session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.000'),
        )
        SessionAnnotation.objects.create(
            session=self.session,
            timestamp_seconds=Decimal('1.500'),
            title='Mark',
            note='CowLog annotation line',
            color='#f59e0b',
            created_by=self.user,
        )
        fps_definition = IndependentVariableDefinition.objects.create(
            project=self.project,
            label='fps',
            value_type=IndependentVariableDefinition.TYPE_NUMERIC,
        )
        ObservationVariableValue.objects.create(
            session=self.session,
            definition=fps_definition,
            value='30',
        )
        response = self.client.get(
            reverse('tracker:session_export_cowlog_txt', args=[self.session.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('CowLog-compatible', response.content.decode('utf-8'))
        self.assertIn('# extension_profile\t1.0', response.content.decode('utf-8'))
        self.assertIn('# observer\tolivier', response.content.decode('utf-8'))
        self.assertIn('# fps\t30', response.content.decode('utf-8'))
        self.assertIn(
            '# annotation\t1.5\tMark\tCowLog annotation line',
            response.content.decode('utf-8'),
        )
        response = self.client.get(
            reverse('tracker:session_export_behavioral_sequences', args=[self.session.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('# observation id:', response.content.decode('utf-8'))
        response = self.client.get(
            reverse('tracker:session_export_textgrid', args=[self.session.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('TextGrid', response.content.decode('utf-8'))
        response = self.client.get(
            reverse('tracker:session_export_binary_table_tsv', args=[self.session.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('time\tEat\tStand', response.content.decode('utf-8'))
        response = self.client.get(
            reverse('tracker:session_export_boris_aggregated_tsv', args=[self.session.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Observation id\tObservation date', response.content.decode('utf-8'))
        self.assertIn('FPS (frame/s)', response.content.decode('utf-8'))
        response = self.client.get(
            reverse('tracker:session_export_boris_tabular_tsv', args=[self.session.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f'session_{self.session.pk}_boris_tabular_events.tsv',
            response['Content-Disposition'],
        )
        self.assertIn('Observation id\tObservation date', response.content.decode('utf-8'))
        self.assertIn('Behavior type\tTime', response.content.decode('utf-8'))
        response = self.client.get(
            reverse('tracker:session_export_feral_json', args=[self.session.pk])
        )
        self.assertEqual(response.status_code, 200)
        feral_payload = json.loads(response.content.decode('utf-8'))
        self.assertFalse(feral_payload['is_multilabel'])
        self.assertIn('class_names', feral_payload)
        response = self.client.get(
            reverse('tracker:session_export_compatibility_report', args=[self.session.pk])
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content.decode('utf-8'))
        self.assertEqual(payload['schema'], 'pybehaviorlog-0.9.5-session-compatibility-report')
        response = self.client.get(
            reverse('tracker:session_export_boris_native', args=[self.session.pk, '9'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('.boris', response['Content-Disposition'])
        payload = json.loads(response.content.decode('utf-8'))
        self.assertEqual(payload['project_format_version'], '7.0')
        self.assertIn('Session 1', payload['observations'])
        response = self.client.get(
            reverse('tracker:project_export_boris_native', args=[self.project.pk, '7'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('.boris', response['Content-Disposition'])
        payload = json.loads(response.content.decode('utf-8'))
        self.assertEqual(payload['project_format_version'], '7.0')

    def test_project_compatibility_report_includes_schema_matrix(self):
        payload = build_project_compatibility_report(self.project)
        self.assertIn('supported_schema_matrix', payload)
        self.assertIn('session_patterns', payload['supported_schema_matrix'])
        self.assertIn('native_boris_project_boris9', payload['supported_boris_exports'])
        self.assertIn('tabular_events', payload['supported_boris_exports'])
        self.assertIn('extension_profile', payload)
        self.assertIn('cowcloud', payload)
        self.assertFalse(payload['cowcloud']['ready'])
        self.assertEqual(payload['extension_profile']['profile_version'], '1.0')
