from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io
from django.contrib.auth.forms import AuthenticationForm


User = get_user_model()

BS = 'form-control'  # raccourci Bootstrap class

class SignupForm(UserCreationForm):
    
    email = forms.EmailField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "email",
            "password1",
            "password2",
        )


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Téléphone",
        widget=forms.TextInput(attrs={'class': BS, 'placeholder': '+229 XXXXXXXX'})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': BS, 'placeholder': 'Mot de passe'})
    )