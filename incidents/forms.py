import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Incident, IncidentAttachment
from accounts.models import CustomUser

class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'title', 'incident_type', 'occurrence_date', 'location',
            'aircraft_registration', 'flight_number', 'description',
            'immediate_actions_taken', 'potential_consequences', 'actual_consequences',
            'initial_severity', 'initial_likelihood'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Near runway incursion at taxiway Bravo during low visibility'}),
            'incident_type': forms.Select(attrs={'class': 'form-select'}),
            'occurrence_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. KJFK Runway 04L / Gate B22'}),
            'aircraft_registration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. N102AA (optional)'}),
            'flight_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. AA482 (optional)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide a detailed, objective account of the occurrence...'}),
            'immediate_actions_taken': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Immediate containment or emergency measures taken...'}),
            'potential_consequences': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Realistic potential worse-case outcome...'}),
            'actual_consequences': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Actual observed damage, delays, or injuries...'}),
            'initial_severity': forms.Select(attrs={'class': 'form-select', 'id': 'id_severity'}),
            'initial_likelihood': forms.Select(attrs={'class': 'form-select', 'id': 'id_likelihood'}),
        }

class IncidentEditForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'title', 'incident_type', 'occurrence_date', 'location',
            'aircraft_registration', 'flight_number', 'description',
            'immediate_actions_taken', 'potential_consequences', 'actual_consequences',
            'initial_severity', 'initial_likelihood'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'incident_type': forms.Select(attrs={'class': 'form-select'}),
            'occurrence_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'aircraft_registration': forms.TextInput(attrs={'class': 'form-control'}),
            'flight_number': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'immediate_actions_taken': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'potential_consequences': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'actual_consequences': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'initial_severity': forms.Select(attrs={'class': 'form-select'}),
            'initial_likelihood': forms.Select(attrs={'class': 'form-select'}),
        }

class IncidentAssignInvestigatorForm(forms.ModelForm):
    assigned_investigator = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(
            role__in=[CustomUser.ROLE_INVESTIGATOR, CustomUser.ROLE_SAFETY_MANAGER],
            is_active=True
        ),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Incident
        fields = ['assigned_investigator']

class IncidentTransitionForm(forms.Form):
    to_status = forms.ChoiceField(
        choices=Incident.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Provide justification, handover notes, or closure rationale...'
        })
    )
    force_override = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Management Override (Allow closure despite incomplete items)'
    )

class IncidentAttachmentForm(forms.ModelForm):
    class Meta:
        model = IncidentAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description (e.g. FDR chart, damage photo)'}),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if not uploaded_file:
            raise ValidationError("Please choose a file to upload.")

        # Validate file size
        if uploaded_file.size > IncidentAttachment.MAX_FILE_SIZE:
            raise ValidationError(f"File size exceeds 10 MB limit ({uploaded_file.size / (1024*1024):.1f} MB uploaded).")

        # Validate file extension
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in IncidentAttachment.ALLOWED_EXTENSIONS:
            allowed = ', '.join(IncidentAttachment.ALLOWED_EXTENSIONS)
            raise ValidationError(f"File extension '{ext}' is not permitted. Permitted types: {allowed}")

        return uploaded_file
