from django.contrib import admin
from .models import Produits

# Register your models here.
@admin.register(Produits) 
class ProduitsAdmin(admin.ModelAdmin):
    list_display = ['nom','prix','image_url', 'date_ajout']