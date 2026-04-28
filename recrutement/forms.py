from django import forms
from .models import Mission, Candidature, Competence


class MissionForm(forms.ModelForm):
    """Formulaire de création / modification d'une mission d'intérim."""

    # Champ Many-to-Many avec cases à cocher
    competences = forms.ModelMultipleChoiceField(
        queryset=Competence.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Compétences requises",
    )

    class Meta:
        model = Mission
        fields = [
            "titre", "description",
            "date_debut", "date_fin",
            "heure", "taux_horaire",
            "competences", "lieu", "image",
        ]
        widgets = {
            "titre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex : Agent d'entretien – Cotonou",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Décrivez la mission, les responsabilités, les conditions…",
            }),
            "date_debut": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "date_fin": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "heure": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
            "taux_horaire": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Ex : 1500",
                "min": "0",
                "step": "50",
            }),
            "lieu": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex : Cotonou, Porto-Novo…",
            }),
            "image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
        }
        labels = {
            "titre":        "Titre de la mission *",
            "description":  "Description *",
            "date_debut":   "Date de début *",
            "date_fin":     "Date de fin *",
            "heure":        "Heure de début *",
            "taux_horaire": "Taux horaire (CFA) *",
            "lieu":         "Lieu *",
            "image":        "Image / Illustration",
        }

    def clean(self):
        cleaned = super().clean()
        date_debut = cleaned.get("date_debut")
        date_fin   = cleaned.get("date_fin")
        if date_debut and date_fin and date_fin < date_debut:
            self.add_error("date_fin", "La date de fin doit être après la date de début.")
        return cleaned


class CandidatureForm(forms.ModelForm):
    """Formulaire de candidature à une mission."""

    class Meta:
        model  = Candidature
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Présentez-vous et expliquez pourquoi vous êtes le candidat idéal…",
            }),
        }
        labels = {"message": "Message de motivation (optionnel)"}


class CompetenceForm(forms.ModelForm):
    """Formulaire d'ajout d'une compétence au répertoire."""

    class Meta:
        model  = Competence
        fields = ["nom"]
        widgets = {
            "nom": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex : Cuisinier, Chauffeur, Comptable…",
            }),
        }
        labels = {"nom": "Nom de la compétence *"}
