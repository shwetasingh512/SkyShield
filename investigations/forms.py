from django import forms
from .models import Investigation, RootCauseAnalysis, ContributingFactor

class InvestigationStartForm(forms.ModelForm):
    class Meta:
        model = Investigation
        fields = ['objectives', 'start_date']
        widgets = {
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Outline the scope and formal safety objectives for this investigation...'
            }),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class InvestigationForm(forms.ModelForm):
    class Meta:
        model = Investigation
        fields = ['objectives', 'findings', 'evidence_reviewed', 'proposed_root_causes', 'investigator_notes']
        widgets = {
            'objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'findings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Document factual sequence of events, operational discrepancies, and verified data points...'
            }),
            'evidence_reviewed': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'List telemetry data, DFDR / CVR extracts, maintenance records, ATC audio logs...'
            }),
            'proposed_root_causes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Synthesize primary root causes deduced from factual findings...'
            }),
            'investigator_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal investigator notes, witness testimony summaries...'
            }),
        }

class InvestigationReviewForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[
            (Investigation.STATUS_APPROVED, 'Approve Investigation (Complete Findings)'),
            (Investigation.STATUS_REJECTED, 'Return / Reject (Further Inquiry Required)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Investigation
        fields = ['status', 'review_comments']
        widgets = {
            'review_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'State formal review assessment, regulatory concurrence, or items needing re-investigation...'
            }),
        }

class RootCauseAnalysisForm(forms.ModelForm):
    class Meta:
        model = RootCauseAnalysis
        fields = [
            'problem_statement',
            'why_1', 'why_2', 'why_3', 'why_4', 'why_5',
            'root_cause_summary', 'preventive_recommendation'
        ]
        widgets = {
            'problem_statement': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Describe the specific event or deviation that triggered the safety incident.'}),
            'why_1': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Direct Trigger: Why did the problem directly happen?'}),
            'why_2': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Direct Condition: Why did the condition in Why #1 exist?'}),
            'why_3': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Underlying Factor: Why did the condition in Why #2 occur?'}),
            'why_4': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Defense Barrier Failure: Why did existing safety barriers fail to stop Why #3?'}),
            'why_5': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Latent Systemic Flaw: Why did organizational management/policy allow Why #4?'}),
            'root_cause_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Synthesized root cause statement.'}),
            'preventive_recommendation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Targeted recommendation to prevent recurrence.'}),
        }

class ContributingFactorForm(forms.ModelForm):
    class Meta:
        model = ContributingFactor
        fields = ['category', 'impact_level', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'impact_level': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Specific contributing circumstances or conditions...'}),
        }
