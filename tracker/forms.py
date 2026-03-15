
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import (
    Behavior,
    BehaviorCategory,
    IndependentVariableDefinition,
    Modifier,
    ObservationSession,
    ObservationVariableValue,
    Project,
    Subject,
    VideoAsset,
)


User = get_user_model()


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class ProjectSettingsForm(forms.ModelForm):
    collaborators = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'collaborators']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = User.objects.order_by('username')
        if owner is not None:
            queryset = queryset.exclude(pk=owner.pk)
        self.fields['collaborators'].queryset = queryset


class EthogramImportForm(forms.Form):
    file = forms.FileField(help_text='Fichier JSON exporté depuis CowLog Django V4/V5/V6 ou format BORIS-like.')
    replace_existing = forms.BooleanField(
        required=False,
        label='Remplacer complètement les éléments d’éthogramme existants',
        help_text='Bloqué si le projet contient déjà des sessions ou des événements.',
    )


class SessionImportForm(forms.Form):
    file = forms.FileField(help_text='JSON V5/V6 ou export BORIS-like simplifié.')
    clear_existing = forms.BooleanField(
        required=False,
        label='Supprimer les événements et annotations existants avant import',
    )


class BehaviorCategoryForm(forms.ModelForm):
    class Meta:
        model = BehaviorCategory
        fields = ['name', 'color', 'sort_order']
        widgets = {'color': forms.TextInput(attrs={'type': 'color'})}


class ModifierForm(forms.ModelForm):
    class Meta:
        model = Modifier
        fields = ['name', 'description', 'key_binding', 'sort_order']
        widgets = {
            'description': forms.TextInput(),
            'key_binding': forms.TextInput(attrs={'maxlength': 1}),
        }

    def clean_key_binding(self):
        return self.cleaned_data['key_binding'].upper()


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description', 'key_binding', 'color', 'sort_order']
        widgets = {
            'description': forms.TextInput(),
            'key_binding': forms.TextInput(attrs={'maxlength': 1}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def clean_key_binding(self):
        return (self.cleaned_data.get('key_binding') or '').upper()


class IndependentVariableDefinitionForm(forms.ModelForm):
    class Meta:
        model = IndependentVariableDefinition
        fields = ['label', 'description', 'value_type', 'set_values', 'default_value', 'sort_order']
        widgets = {
            'description': forms.TextInput(),
            'set_values': forms.Textarea(attrs={'rows': 3}),
            'default_value': forms.TextInput(),
        }


class BehaviorForm(forms.ModelForm):
    class Meta:
        model = Behavior
        fields = ['category', 'name', 'description', 'key_binding', 'color', 'mode', 'sort_order']
        widgets = {
            'description': forms.TextInput(),
            'key_binding': forms.TextInput(attrs={'maxlength': 1}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        if project is not None:
            self.fields['category'].queryset = project.categories.all()

    def clean_key_binding(self):
        return self.cleaned_data['key_binding'].upper()


class VideoAssetForm(forms.ModelForm):
    class Meta:
        model = VideoAsset
        fields = ['title', 'file', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['file'].required = False


class ObservationSessionForm(forms.ModelForm):
    additional_videos = forms.ModelMultipleChoiceField(
        queryset=VideoAsset.objects.none(),
        required=False,
        help_text='Vidéos secondaires synchronisées avec la vidéo principale.',
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = ObservationSession
        fields = [
            'session_kind', 'video', 'additional_videos', 'title', 'description',
            'playback_rate', 'frame_step_seconds', 'recorded_at', 'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'recorded_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project is not None:
            video_qs = project.videos.order_by('title')
            self.fields['video'].queryset = video_qs
            self.fields['additional_videos'].queryset = video_qs
            for definition in project.variable_definitions.order_by('sort_order', 'label'):
                field_name = f'var_{definition.pk}'
                if definition.value_type == IndependentVariableDefinition.TYPE_NUMERIC:
                    field = forms.DecimalField(required=False, label=definition.label)
                elif definition.value_type == IndependentVariableDefinition.TYPE_SET:
                    choices = [('', '---------')] + [(item, item) for item in definition.value_options]
                    field = forms.ChoiceField(required=False, label=definition.label, choices=choices)
                elif definition.value_type == IndependentVariableDefinition.TYPE_TIMESTAMP:
                    field = forms.DateTimeField(
                        required=False,
                        label=definition.label,
                        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                    )
                else:
                    field = forms.CharField(required=False, label=definition.label)
                help_text = definition.description or ''
                if definition.value_type == IndependentVariableDefinition.TYPE_SET and definition.set_values:
                    help_text = (help_text + ' ' if help_text else '') + f'Valeurs possibles : {definition.set_values}'
                field.help_text = help_text
                self.fields[field_name] = field
                initial_value = definition.default_value
                if self.instance and self.instance.pk:
                    existing = self.instance.variable_values.filter(definition=definition).first()
                    if existing:
                        initial_value = existing.value
                self.fields[field_name].initial = initial_value
        if self.instance and self.instance.pk:
            linked_ids = list(
                self.instance.video_links.exclude(video=self.instance.video).values_list('video_id', flat=True)
            )
            self.fields['additional_videos'].initial = linked_ids
            if self.instance.recorded_at:
                self.initial['recorded_at'] = self.instance.recorded_at.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        session_kind = cleaned_data.get('session_kind')
        video = cleaned_data.get('video')
        if session_kind == ObservationSession.KIND_MEDIA and video is None:
            self.add_error('video', 'Une vidéo principale est requise pour une session média.')
        if session_kind == ObservationSession.KIND_LIVE:
            cleaned_data['video'] = None
            cleaned_data['additional_videos'] = []
        return cleaned_data

    def save_variable_values(self, session):
        if not self.project:
            return
        for definition in self.project.variable_definitions.order_by('sort_order', 'label'):
            field_name = f'var_{definition.pk}'
            value = self.cleaned_data.get(field_name, '')
            if value is None:
                value = ''
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            ObservationVariableValue.objects.update_or_create(
                session=session,
                definition=definition,
                defaults={'value': str(value)},
            )


class DeleteConfirmForm(forms.Form):
    confirm = forms.BooleanField(label='Je confirme la suppression')
