from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()

class SearchForm(forms.Form):
    query = forms.CharField(max_length=255)