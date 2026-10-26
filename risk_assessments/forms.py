from django import forms
from .models import RiskAssessment, RiskThresholdConfig

class RiskAssessmentForm(forms.ModelForm):
    class Meta:
        model = RiskAssessment
        fields = ['assessment_type', 'likelihood', 'severity', 'rationale', 'mitigation_notes']
        widgets = {
            'assessment_type': forms.Select(attrs={'class': 'form-select'}),
            'likelihood': forms.Select(attrs={'class': 'form-select', 'id': 'id_likelihood'}),
            'severity': forms.Select(attrs={'class': 'form-select', 'id': 'id_severity'}),
            'rationale': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'State clearly the basis for assigning these ratings based on evidence, history, or flight data.'}),
            'mitigation_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Immediate mitigating steps or containment applied.'}),
        }

class RiskThresholdConfigForm(forms.ModelForm):
    class Meta:
        model = RiskThresholdConfig
        fields = ['band_name', 'min_score', 'max_score', 'color_code', 'description', 'action_required']
        widgets = {
            'band_name': forms.Select(attrs={'class': 'form-select'}),
            'min_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 25}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 25}),
            'color_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#28a745'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'action_required': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
