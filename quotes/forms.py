from django import forms

from .models import Quote


class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["design"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep manual quote requests tied to a specific custom design.
        self.fields["design"].required = True


class QuoteUpdateForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["price", "status"]
