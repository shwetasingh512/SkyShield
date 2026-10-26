from django import forms
from django.utils import timezone
from .models import CorrectiveAction
from accounts.models import CustomUser

class CorrectiveActionCreateForm(forms.ModelForm):
    responsible_user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('username'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CorrectiveAction
        fields = ['action_type', 'title', 'description', 'responsible_user', 'priority', 'due_date']
        widgets = {
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Issue Flight Operations Bulletin FOB-2026-04 on winter braking action'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe required execution steps, responsible department, and verification metrics...'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError("Action due date cannot be set in the past.")
        return due_date

class CorrectiveActionProgressForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[
            (CorrectiveAction.STATUS_IN_PROGRESS, 'In Progress (Active Work Underway)'),
            (CorrectiveAction.STATUS_PENDING_VERIFICATION, 'Ready for Safety Manager Verification (Work Complete)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CorrectiveAction
        fields = ['status', 'completion_evidence']
        widgets = {
            'completion_evidence': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide specific proof of implementation: bulletin number, sign-off sheet, training record...'
            }),
        }

class CorrectiveActionVerifyForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[
            ('APPROVE', 'Verify and Complete Action (Closure Approved)'),
            ('REJECT', 'Reject / Request Rework (Action Remains Open)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    verification_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Document Safety Manager validation criteria, inspection audit, or rework feedback...'
        })
    )
