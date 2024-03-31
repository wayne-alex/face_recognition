from django import forms
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm

from .models import *


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        label=''
    )

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
        label=''
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        label=''
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        # Remove labels and help text for all fields
        for field_name in self.fields:
            self.fields[field_name].label = ''
            self.fields[field_name].help_text = ''

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Registration Number'

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Enter Password'

        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'


class EditUserForm(forms.Form):
    turn = forms.IntegerField()
    status = forms.ChoiceField(choices=[('verify', 'verify'), ('reject', 'reject')],
                               widget=forms.Select(attrs={'class': 'form-select'}))


