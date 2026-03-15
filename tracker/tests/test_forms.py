
from django.contrib.auth import get_user_model
from django.test import TestCase

from tracker.forms import ObservationSessionForm
from tracker.models import (
    IndependentVariableDefinition,
    Project,
    VideoAsset,
)


User = get_user_model()


class ObservationSessionFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='olivier', password='pass12345')
        self.project = Project.objects.create(owner=self.user, name='Projet 1')
        self.video = VideoAsset.objects.create(project=self.project, title='Vid 1', file='videos/test.mp4')
        IndependentVariableDefinition.objects.create(
            project=self.project,
            label='Weather',
            value_type=IndependentVariableDefinition.TYPE_SET,
            set_values='sunny,cloudy',
            default_value='sunny',
        )

    def test_media_session_requires_video(self):
        form = ObservationSessionForm(
            data={
                'session_kind': 'media',
                'title': 'Session 1',
                'playback_rate': '1.00',
                'frame_step_seconds': '0.0400',
                'recorded_at': '2026-03-15T10:00',
                'var_1': 'sunny',
            },
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('video', form.errors)

    def test_live_session_is_valid_without_video(self):
        form = ObservationSessionForm(
            data={
                'session_kind': 'live',
                'title': 'Session 1',
                'playback_rate': '1.00',
                'frame_step_seconds': '0.0400',
                'recorded_at': '2026-03-15T10:00',
                'var_1': 'cloudy',
            },
            project=self.project,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_media_session_with_video_is_valid(self):
        form = ObservationSessionForm(
            data={
                'session_kind': 'media',
                'video': self.video.pk,
                'title': 'Session 1',
                'playback_rate': '1.00',
                'frame_step_seconds': '0.0400',
                'recorded_at': '2026-03-15T10:00',
                'var_1': 'sunny',
            },
            project=self.project,
        )
        self.assertTrue(form.is_valid(), form.errors)
