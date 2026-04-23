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
    nom = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    prenoms = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    photo_url = forms.ImageField(
        widget=forms.FileInput(attrs={"class": "form-control","accept": "image/*"})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "email",
            "nom",
            "prenoms",
            "photo_url",
            "password1",
            "password2",
        )


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': BS, 'placeholder': 'abc123@gmail'})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': BS, 'placeholder': 'Mot de passe'})
    )


class ProfileUpdateForm(forms.ModelForm):
    """MAJ profil + upload photo avec redimensionnement"""

    class Meta:
        model = User
        fields = ['nom', 'prenoms','photo_url']
        widgets = {
            'nom':             forms.TextInput(attrs={'class': BS}),
            'prenoms':         forms.TextInput(attrs={'class': BS}),
            'photo_url':        forms.FileInput(attrs={'class': BS, 'accept': 'image/*'}),
        }

    def clean_photo_url(self):
        image = self.cleaned_data.get('photo_url')

        if not image:
            return image

        # Vérification format
        allowed = ['image/jpeg', 'image/png', 'image/webp']
        if hasattr(image, 'content_type') and image.content_type not in allowed:
            raise forms.ValidationError("Format accepté : JPG, PNG, WEBP uniquement.")

        # Redimensionnement avec Pillow
        img = Image.open(image)
        img = img.convert('RGB')  # Forcer RGB (évite les PNG RGBA)

        # Resize : max 800x600, conserve le ratio
        img.thumbnail((800, 600), Image.LANCZOS)

        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)

        return InMemoryUploadedFile(
            output,
            'ImageField',
            f"{image.name.split('.')[0]}.jpg",
            'image/jpeg',
            output.getbuffer().nbytes,
            None
        )
