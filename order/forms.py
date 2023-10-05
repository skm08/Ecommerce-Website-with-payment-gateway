from django import forms

class CheckoutForm(forms.Form):
    first_name=forms.CharField(max_length=256)
    last_name=forms.CharField(max_length=256)
    email=forms.EmailField(max_length=256)
    city=forms.CharField(max_length=256)
    zip_code=forms.CharField(max_length=256)
    address=forms.CharField(widget=forms.Textarea)