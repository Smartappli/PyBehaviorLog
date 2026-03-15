
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from tracker.models import (
    Behavior,
    BehaviorCategory,
    IndependentVariableDefinition,
    Modifier,
    ObservationEvent,
    ObservationSession,
    Project,
    Subject,
    VideoAsset,
)


User = get_user_model()


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='olivier', password='pass12345')
        self.project = Project.objects.create(owner=self.user, name='Projet 1')
        self.category = BehaviorCategory.objects.create(project=self.project, name='General')
        self.behavior = Behavior.objects.create(
            project=self.project,
            category=self.category,
            name='Eat',
            key_binding='e',
            mode=Behavior.MODE_POINT,
        )
        self.modifier = Modifier.objects.create(
            project=self.project,
            name='Near',
            key_binding='n',
        )
        self.subject = Subject.objects.create(
            project=self.project,
            name='Cow 1',
            key_binding='c',
        )
        self.variable = IndependentVariableDefinition.objects.create(
            project=self.project,
            label='Weather',
            value_type=IndependentVariableDefinition.TYPE_SET,
            set_values='sunny,cloudy,rainy',
            default_value='sunny',
        )

    def test_uppercase_key_bindings(self):
        self.assertEqual(self.behavior.key_binding, 'E')
        self.assertEqual(self.modifier.key_binding, 'N')
        self.assertEqual(self.subject.key_binding, 'C')

    def test_value_options(self):
        self.assertEqual(self.variable.value_options, ['sunny', 'cloudy', 'rainy'])

    def test_session_primary_label_for_live(self):
        session = ObservationSession.objects.create(
            project=self.project,
            observer=self.user,
            title='Live 1',
            session_kind=ObservationSession.KIND_LIVE,
        )
        self.assertEqual(session.primary_label, 'LIVE')
        self.assertEqual(session.all_videos_ordered, [])

    def test_session_primary_label_for_media(self):
        video = VideoAsset.objects.create(project=self.project, title='Vid 1', file='videos/test.mp4')
        session = ObservationSession.objects.create(
            project=self.project,
            observer=self.user,
            title='Media 1',
            session_kind=ObservationSession.KIND_MEDIA,
            video=video,
        )
        self.assertEqual(session.primary_label, 'Vid 1')

    def test_event_with_subject_and_frame(self):
        session = ObservationSession.objects.create(
            project=self.project,
            observer=self.user,
            title='Observation',
            session_kind=ObservationSession.KIND_LIVE,
        )
        event = ObservationEvent.objects.create(
            session=session,
            behavior=self.behavior,
            subject=self.subject,
            event_kind=ObservationEvent.KIND_POINT,
            timestamp_seconds=Decimal('1.250'),
            frame_index=31,
        )
        self.assertEqual(event.subject.name, 'Cow 1')
        self.assertEqual(event.frame_index, 31)
