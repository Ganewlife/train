from django import forms
from django.core.exceptions import ValidationError
from .models import Media, Category, Tag

# Types MIME autorisés par catégorie
ALLOWED_VIDEO_TYPES = [
    "video/mp4", "video/avi", "video/x-msvideo",
    "video/quicktime", "video/x-matroska", "video/webm",
]
ALLOWED_IMAGE_TYPES = [
    "image/jpeg", "image/png", "image/webp",
    "image/gif", "image/svg+xml",
]
ALLOWED_AUDIO_TYPES = [
    "audio/mpeg", "audio/wav", "audio/flac",
    "audio/ogg", "audio/aac", "audio/x-m4a",
]
ALL_ALLOWED_TYPES = ALLOWED_VIDEO_TYPES + ALLOWED_IMAGE_TYPES + ALLOWED_AUDIO_TYPES

# Taille max : 2 Go
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024


class MediaUploadForm(forms.ModelForm):
    """Formulaire principal de téléversement de média avec métadonnées."""

    tags_input = forms.CharField(
        required=False,
        label="Mots-clés",
        widget=forms.TextInput(attrs={
            "placeholder": "django, python, web… (séparés par des virgules)",
            "class": "sv-input",
        }),
        help_text="Séparez les mots-clés par des virgules.",
    )

    class Meta:
        model = Media
        fields = [
            "title", "media_type", "file", "thumbnail",
            "category", "author", "production_date",
            "description", "visibility", "license",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "Ex : Introduction à Django",
                "class": "sv-input",
            }),
            "media_type": forms.Select(attrs={"class": "sv-input sv-select"}),
            "file": forms.FileInput(attrs={"class": "sv-file-input", "id": "id_file"}),
            "thumbnail": forms.FileInput(attrs={
                "class": "sv-file-input",
                "accept": "image/*",
            }),
            "category": forms.Select(attrs={"class": "sv-input sv-select"}),
            "author": forms.TextInput(attrs={
                "placeholder": "Nom de l'auteur ou du réalisateur",
                "class": "sv-input",
            }),
            "production_date": forms.DateInput(attrs={
                "type": "date",
                "class": "sv-input",
            }),
            "description": forms.Textarea(attrs={
                "placeholder": "Décrivez le contenu de ce média pour faciliter l'indexation…",
                "class": "sv-input sv-textarea",
                "rows": 4,
            }),
            "visibility": forms.Select(attrs={"class": "sv-input sv-select"}),
            "license": forms.Select(attrs={"class": "sv-input sv-select"}),
        }
        labels = {
            "title": "Titre *",
            "media_type": "Type de média *",
            "file": "Fichier *",
            "thumbnail": "Miniature (optionnel)",
            "category": "Catégorie",
            "author": "Auteur / Réalisateur",
            "production_date": "Date de production",
            "description": "Description",
            "visibility": "Visibilité",
            "license": "Licence",
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            raise ValidationError("Veuillez sélectionner un fichier.")

        # Vérification taille
        if file.size > MAX_FILE_SIZE:
            raise ValidationError(
                f"Le fichier est trop volumineux ({file.size / (1024**3):.1f} Go). "
                f"Taille maximale : 2 Go."
            )

        # Vérification type MIME
        content_type = getattr(file, "content_type", "")
        if content_type and content_type not in ALL_ALLOWED_TYPES:
            raise ValidationError(
                f"Type de fichier non autorisé : {content_type}. "
                "Formats acceptés : MP4, AVI, MOV, MKV, WebM, JPG, PNG, WebP, MP3, WAV, FLAC."
            )

        return file

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get("thumbnail")
        if thumbnail:
            if thumbnail.size > 10 * 1024 * 1024:  # 10 Mo max
                raise ValidationError("La miniature ne doit pas dépasser 10 Mo.")
            content_type = getattr(thumbnail, "content_type", "")
            if content_type and content_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError("La miniature doit être une image (JPG, PNG, WebP).")
        return thumbnail

    def clean(self):
        cleaned = super().clean()
        file = cleaned.get("file")
        media_type = cleaned.get("media_type")

        if file and media_type:
            content_type = getattr(file, "content_type", "")
            type_map = {
                Media.TYPE_VIDEO: ALLOWED_VIDEO_TYPES,
                Media.TYPE_IMAGE: ALLOWED_IMAGE_TYPES,
                Media.TYPE_AUDIO: ALLOWED_AUDIO_TYPES,
            }
            allowed = type_map.get(media_type, [])
            if content_type and allowed and content_type not in allowed:
                self.add_error(
                    "file",
                    f"Le fichier sélectionné ne correspond pas au type « {media_type} ».",
                )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Calcul automatique de la taille
        if instance.file:
            try:
                instance.file_size = instance.file.size
            except Exception:
                pass

        if commit:
            instance.save()
            # Gestion des tags depuis le champ texte libre
            tags_raw = self.cleaned_data.get("tags_input", "")
            if tags_raw:
                instance.tags.clear()
                for tag_name in tags_raw.split(","):
                    tag_name = tag_name.strip().lower()
                    if tag_name:
                        tag, _ = Tag.objects.get_or_create(name=tag_name)
                        instance.tags.add(tag)
        return instance


class MediaEditForm(MediaUploadForm):
    """Formulaire d'édition (le fichier est optionnel)."""

    class Meta(MediaUploadForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = False
        # Pré-remplir les tags
        if self.instance and self.instance.pk:
            existing = ", ".join(self.instance.tags.values_list("name", flat=True))
            self.fields["tags_input"].initial = existing

    def clean_file(self):
        file = self.cleaned_data.get("file")
        # En édition, le fichier est optionnel
        if not file:
            return self.instance.file if self.instance else None
        # Sinon on applique les mêmes validations
        return super().clean_file()


class MediaSearchForm(forms.Form):
    """Formulaire de recherche avancée."""

    q = forms.CharField(
        required=False,
        label="Recherche",
        max_length=200,
        widget=forms.TextInput(attrs={
            "placeholder": "Rechercher par titre, auteur, mot-clé…",
            "class": "sv-input sv-search-input",
            "autocomplete": "off",
        }),
    )

    media_type = forms.ChoiceField(
        required=False,
        label="Type",
        choices=[("", "Tous les types")] + Media.MEDIA_TYPES,
        widget=forms.Select(attrs={"class": "sv-input sv-select"}),
    )

    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        label="Catégorie",
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={"class": "sv-input sv-select"}),
    )

    date_from = forms.DateField(
        required=False,
        label="Du",
        widget=forms.DateInput(attrs={"type": "date", "class": "sv-input"}),
    )

    date_to = forms.DateField(
        required=False,
        label="Au",
        widget=forms.DateInput(attrs={"type": "date", "class": "sv-input"}),
    )

    sort = forms.ChoiceField(
        required=False,
        label="Trier par",
        choices=[
            ("-created_at", "Plus récents"),
            ("created_at", "Plus anciens"),
            ("title", "Nom A–Z"),
            ("-title", "Nom Z–A"),
            ("-view_count", "Plus consultés"),
        ],
        widget=forms.Select(attrs={"class": "sv-input sv-select"}),
    )

    visibility = forms.ChoiceField(
        required=False,
        label="Visibilité",
        choices=[("", "Toutes"), ("public", "Publics"), ("private", "Privés")],
        widget=forms.Select(attrs={"class": "sv-input sv-select"}),
    )
