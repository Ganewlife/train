from django.db import models
# from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
import os
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom")
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


def media_upload_path(instance, filename):
    """Organise les fichiers par type et utilisateur."""
    ext = filename.rsplit(".", 1)[-1].lower()
    folder = instance.media_type
    return f"media/{folder}/{instance.uploaded_by.id}/{filename}"


def thumbnail_upload_path(instance, filename):
    return f"thumbnails/{instance.uploaded_by.id}/{filename}"


class Media(models.Model):
    TYPE_VIDEO = "video"
    TYPE_IMAGE = "image"
    TYPE_AUDIO = "audio"

    MEDIA_TYPES = [
        (TYPE_VIDEO, "Vidéo"),
        (TYPE_IMAGE, "Image"),
        (TYPE_AUDIO, "Audio"),
    ]

    VISIBILITY_PUBLIC = "public"
    VISIBILITY_PRIVATE = "private"
    VISIBILITY_INVITE = "invite"

    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, "Public"),
        (VISIBILITY_PRIVATE, "Privé"),
        (VISIBILITY_INVITE, "Sur invitation"),
    ]

    LICENSE_CHOICES = [
        ("proprietary", "Propriétaire"),
        ("cc_by", "CC BY"),
        ("cc_by_sa", "CC BY-SA"),
        ("public_domain", "Domaine public"),
    ]

    # Informations principales
    title = models.CharField(max_length=255, verbose_name="Titre")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Description")
    media_type = models.CharField(
        max_length=10, choices=MEDIA_TYPES, verbose_name="Type de média"
    )

    # Fichiers
    file = models.FileField(
        upload_to=media_upload_path, verbose_name="Fichier média"
    )
    thumbnail = models.ImageField(
        upload_to=thumbnail_upload_path,
        blank=True,
        null=True,
        verbose_name="Miniature",
    )

    # Métadonnées
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medias",
        verbose_name="Catégorie",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="medias", verbose_name="Tags")
    author = models.CharField(max_length=200, blank=True, verbose_name="Auteur / Réalisateur")
    production_date = models.DateField(null=True, blank=True, verbose_name="Date de production")
    duration = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Durée (secondes)"
    )
    file_size = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name="Taille du fichier (octets)"
    )

    # Visibilité & licence
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        verbose_name="Visibilité",
    )
    license = models.CharField(
        max_length=20,
        choices=LICENSE_CHOICES,
        default="proprietary",
        verbose_name="Licence",
    )

    # Relations utilisateurs
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medias",
        verbose_name="Téléversé par",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Média"
        verbose_name_plural = "Médias"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["media_type"]),
            models.Index(fields=["visibility"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Media.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Calcule la taille du fichier automatiquement
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("media:detail", kwargs={"slug": self.slug})

    def get_file_size_display(self):
        """Retourne la taille lisible par un humain."""
        if not self.file_size:
            return "—"
        size = self.file_size
        for unit in ["o", "Ko", "Mo", "Go", "To"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} Po"

    def get_duration_display(self):
        """Retourne la durée formatée MM:SS ou HH:MM:SS."""
        if not self.duration:
            return "—"
        h = self.duration // 3600
        m = (self.duration % 3600) // 60
        s = self.duration % 60
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    @property
    def view_count(self):
        return self.views.count()

    @property
    def is_video(self):
        return self.media_type == self.TYPE_VIDEO

    @property
    def is_image(self):
        return self.media_type == self.TYPE_IMAGE

    @property
    def is_audio(self):
        return self.media_type == self.TYPE_AUDIO


class MediaView(models.Model):
    """Enregistre chaque visualisation d'un média."""
    media = models.ForeignKey(
        Media, on_delete=models.CASCADE, related_name="views"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vue"
        verbose_name_plural = "Vues"

    def __str__(self):
        return f"Vue sur '{self.media.title}' le {self.viewed_at:%d/%m/%Y}"


class SearchLog(models.Model):
    """Journalise les recherches pour améliorer l'algorithme."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    query = models.CharField(max_length=500)
    results_count = models.PositiveIntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recherche"
        verbose_name_plural = "Recherches"
        ordering = ["-searched_at"]

    def __str__(self):
        return f'"{self.query}" ({self.results_count} résultats)'
