from django.contrib import admin
from .models import Mission, Competence, Candidature


@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display  = ["nom"]
    search_fields = ["nom"]


class CandidatureInline(admin.TabularInline):
    model        = Candidature
    extra        = 0
    readonly_fields = ["candidat", "statut", "postule_le"]
    can_delete   = False


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display   = ["titre", "lieu", "date_debut", "date_fin", "statut", "auteur", "nombre_candidats"]
    list_filter    = ["statut", "date_debut"]
    search_fields  = ["titre", "lieu", "description"]
    filter_horizontal = ["competences"]
    readonly_fields   = ["cree_le", "modifie_le"]
    inlines        = [CandidatureInline]

    def nombre_candidats(self, obj):
        return obj.nombre_candidats
    nombre_candidats.short_description = "Candidats"


@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display  = ["candidat", "mission", "statut", "postule_le"]
    list_filter   = ["statut", "postule_le"]
    search_fields = ["candidat__username", "mission__titre"]
