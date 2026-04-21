from django import forms
# from django.contrib.auth import get_user_model
# from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io
# from django.contrib.auth.forms import AuthenticationForm
from .models import Produits

BS = 'form-control'  # raccourci Bootstrap class

class ProduitsForm(forms.ModelForm):
    """ nom = forms.CharField(
        widget=forms.TextInput(attrs={"class": BS})
    )
    prix = forms.DecimalField(
        widget=forms.IntegerField(attrs={"class": BS})
    ) """
    class Meta:
        model = Produits
        fields = ['nom', 'prix', 'image_url']
        widgets = {
            'nom':             forms.TextInput(attrs={'class': BS}),
            'prix':         forms.NumberInput(attrs={'class': BS}),
            'image_url':        forms.FileInput(attrs={'class': BS, 'accept': 'image/*'}),
        }
        
    def clean_image_url(self):
        image = self.cleaned_data.get('image_url')

        if not image:
            return image

        # Vérification format
        allowed = ['image/jpeg', 'image/png', 'image/webp']
        if hasattr(image, 'content_type') and image.content_type not in allowed:
            raise forms.ValidationError("Format accepté : JPG, PNG, WEBP uniquement.")
        
        # Vérification taille fichier (max 5 Mo)
        taille_max = 2 * 1024 * 1024  # 5 Mo en octets
        if image.size > taille_max:
            raise forms.ValidationError(f"Image trop lourde ({image.size // (1024*1024)} Mo). Maximum autorisé : 2 Mo.")

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