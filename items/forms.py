from django import forms
from .models import Item


class ItemReportForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['item_type', 'title', 'description', 'category', 'location', 'date_reported', 'image']
        widgets = {
            'date_reported': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title.strip()) < 3:
            raise forms.ValidationError('Title must be at least 3 characters.')
        return title
