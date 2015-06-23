from django import forms
from django.contrib.auth.models import User
from item.models import UserProfile, Computer

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('website', 'picture')


class ComputerForm(forms.ModelForm):
    class Meta:
        model = Computer
        exclude = ('user', 'created_at', 'updated_at')
