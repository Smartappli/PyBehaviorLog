
import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from tracker.models import Behavior, Project


User = get_user_model()


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='olivier', password='pass12345')
        self.client = Client()
        self.client.login(username='olivier', password='pass12345')
        self.project = Project.objects.create(owner=self.user, name='Projet 1')
        self.behavior = Behavior.objects.create(project=self.project, name='Eat', key_binding='e')

    def test_home_requires_login(self):
        anon = Client()
        response = anon.get(reverse('tracker:home'))
        self.assertEqual(response.status_code, 302)

    def test_home_page(self):
        response = self.client.get(reverse('tracker:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PyBehaviorLog')

    def test_project_create(self):
        response = self.client.post(
            reverse('tracker:project_create'),
            {'name': 'Projet 2', 'description': 'Desc'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(name='Projet 2').exists())

    def test_live_session_create(self):
        response = self.client.post(
            reverse('tracker:session_create', args=[self.project.pk]),
            {
                'session_kind': 'live',
                'title': 'Live session',
                'playback_rate': '1.00',
                'frame_step_seconds': '0.0400',
                'recorded_at': '2026-03-15T10:00',
                'notes': '',
                'description': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.project.sessions.filter(title='Live session').exists())

    def test_event_api_create_and_list(self):
        session = self.project.sessions.create(
            title='Live session',
            observer=self.user,
            session_kind='live',
        )
        response = self.client.post(
            reverse('tracker:event_create_api', args=[session.pk]),
            data=json.dumps({'behavior_id': self.behavior.pk, 'timestamp_seconds': 1.5, 'comment': 'ok'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload['event']['behavior'], 'Eat')

        list_response = self.client.get(reverse('tracker:session_events_json', args=[session.pk]))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()['events']), 1)

    def test_session_json_export(self):
        session = self.project.sessions.create(
            title='Live session',
            observer=self.user,
            session_kind='live',
        )
        self.client.post(
            reverse('tracker:event_create_api', args=[session.pk]),
            data=json.dumps({'behavior_id': self.behavior.pk, 'timestamp_seconds': 1.5}),
            content_type='application/json',
        )
        response = self.client.get(reverse('tracker:session_export_json', args=[session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('pybehaviorlog-v6-session', response.content.decode('utf-8'))
