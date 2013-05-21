from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class Email(forms.EmailField): 
    def clean(self, value):
        super(Email, self).clean(value)
        try:
            User.objects.get(email=value)
            raise forms.ValidationError("This email is already registered. Use the 'forgot password' link on the login page")
        except User.DoesNotExist:
            return value

class UserEmailCreationForm(UserCreationForm):
    email = Email(label="Email", max_length=64)

    def save(self, commit=True):
        user = super(UserEmailForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
