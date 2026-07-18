from django import forms


class ClaimSubmitForm(forms.Form):
    verification_answers = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        min_length=20,
        error_messages={
            'min_length': 'Please provide at least 20 characters describing identifying details.',
            'required': 'Verification answers are required.',
        }
    )
