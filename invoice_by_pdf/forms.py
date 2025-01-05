from django import forms # type: ignore
from .models import InvoiceFile

class InvoiceFileForm(forms.ModelForm):
    class Meta:
        model = InvoiceFile
        fields = ['file']
