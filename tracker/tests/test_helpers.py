
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from tracker.models import Behavior, ObservationEvent, ObservationSession, Project
from tracker.views import build_project_statistics, build_statistics, resolve_event_kind


User = get_user_model()


class HelperTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='olivier', password='pass12345')
        self.project = Project.objects.create(owner=self.user, name='Projet 1')
        self.point_behavior = Behavior.objects.create(project=self.project, name='Eat', key_binding='e')
        self.state_behavior = Behavior.objects.create(
            project=self.project,
            name='Stand',
            key_binding='s',
            mode=Behavior.MODE_STATE,
        )
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

    def test_build_statistics(self):
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
            timestamp_seconds=Decimal('5.000'),
        )
        stats = build_statistics(self.session)
        self.assertEqual(stats['session_event_count'], 3)
        self.assertEqual(stats['point_event_count'], 1)

    def test_build_project_statistics(self):
        ObservationEvent.objects.create(
            session=self.session,
            behavior=self.point_behavior,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.000'),
        )
        analytics = build_project_statistics(self.project)
        self.assertEqual(analytics['session_count'], 1)
        self.assertEqual(analytics['event_count'], 1)
