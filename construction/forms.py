from django import forms

from .models import ConstructionProject, ProgressUpdate


class ConstructionProjectForm(forms.ModelForm):
    class Meta:
        model = ConstructionProject
        fields = [
            "owner",
            "quote",
            "start_date",
            "expected_end_date",
            "total_progress",
        ]


class ProgressUpdateForm(forms.ModelForm):
    class Meta:
        model = ProgressUpdate
        fields = [
            "stage_name",
            "description",
            "site_image",
            "update_date",
        ]
