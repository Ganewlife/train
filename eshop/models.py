from django.db import models
import uuid
import os


# Create your models here.

def rename_image(instance, filename):
    ext = filename.split('.')[-1]  # récupère l'extension originale
    nouveau_nom = f"{uuid.uuid4().hex}.{ext}"  # ex: a3f9c1d2...jpg
    return os.path.join('uploads/', nouveau_nom)


class Produits(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255, blank=False, null=False)
    prix = models.DecimalField(max_digits=10, decimal_places=0, default=0, blank=False, null=False)
    image_url = models.ImageField(upload_to=rename_image)
    
    is_active = models.BooleanField(default=True, auto_created=True)
    date_ajout = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    
    
    