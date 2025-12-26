from django import forms

from .models import HouseDesign


class HouseDesignForm(forms.ModelForm):
    class Meta:
        model = HouseDesign
        fields = [
            "title",
            "description",
            "cover_image",
            "floor_plan",
        ]
