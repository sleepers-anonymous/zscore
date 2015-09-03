from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

illegal_usernames=['friends', 'user', 'anon', 'all']

class Email(forms.EmailField):
    def clean(self, value):
        super(Email, self).clean(value)
        try:
            User.objects.get(email=value)
            raise forms.ValidationError("This email is already registered. Use the 'forgot password' link on the login page")
        except User.DoesNotExist:
            return value

def hasalphanum(s):
    """I want to enforce that all users have at least one alphanumeric character in their username."""
    for i in s:
        if i.isalnum(): return True
    return False

class UserEmailCreationForm(UserCreationForm):
    email = Email(label="Email", max_length=64)

    def clean(self):
        cleaned_data = super(UserEmailCreationForm, self).clean()
        if "username" in cleaned_data and (cleaned_data["username"] in illegal_usernames or (hasalphanum(cleaned_data["username"]) is False)):
            self.add_error("username",
                           "Illegal username! Please pick another!")
        return cleaned_data

    def save(self, commit=True):
        user = super(UserEmailCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
