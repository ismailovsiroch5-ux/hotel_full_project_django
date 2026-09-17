from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Booking


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email manzil")
    first_name = forms.CharField(max_length=50, required=True, label="Ismingiz")
    last_name = forms.CharField(max_length=50, required=True, label="Familiyangiz")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out']
        widgets = {
            'check_in': forms.DateInput(attrs={
                'type': 'date', 
                'id': 'check_in', 
                'class': 'form-control',
                'onchange': 'calculateTotal()'
            }),
            'check_out': forms.DateInput(attrs={
                'type': 'date', 
                'id': 'check_out', 
                'class': 'form-control',
                'onchange': 'calculateTotal()'
            }),
        }