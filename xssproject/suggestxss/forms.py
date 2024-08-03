from django import forms
from .models import UserData
from django import forms

class UserDataForm(forms.ModelForm):
    class Meta:
        model = UserData
        fields = ['goal', 'attackT', 'skill', 'automation', 'platform']

class UploadCSVForm(forms.Form):
    csv_file = forms.FileField()