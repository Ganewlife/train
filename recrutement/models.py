from django.db import models
# from django.contrib.auth.models import User
from django.conf import settings


class Competence(models.Model):
    """Répertoire des compétences disponibles pour les missions."""
    nom = models.CharField(max_length=100, unique=True, verbose_name="Compétence")

    class Meta:
        verbose_name = "Compétence"
        verbose_name_plural = "Compétences"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Mission(models.Model):
    """Mission d'intérim publiée par un recruteur."""

    STATUT_OUVERTE   = "ouverte"
    STATUT_FERMEE    = "fermee"
    STATUT_POURVUE   = "pourvue"

    STATUT_CHOICES = [
        (STATUT_OUVERTE,  "Ouverte"),
        (STATUT_FERMEE,   "Fermée"),
        (STATUT_POURVUE,  "Pourvue"),
    ]

    # Informations principales
    titre       = models.CharField(max_length=200, verbose_name="Titre de la mission")
    description = models.TextField(verbose_name="Description")

    # Dates
    date_debut  = models.DateField(verbose_name="Date de début")
    date_fin    = models.DateField(verbose_name="Date de fin")

    # Horaire & rémunération
    heure       = models.TimeField(verbose_name="Heure de début")
    taux_horaire = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Taux horaire (CFA)"
    )

    # Compétences requises (many-to-many)
    competences = models.ManyToManyField(
        Competence,
        blank=True,
        related_name="missions",
        verbose_name="Compétences requises",
    )

    # Localisation
    lieu        = models.CharField(max_length=200, verbose_name="Lieu")

    # Image / illustration
    image       = models.ImageField(
        upload_to="missions/",
        blank=True,
        null=True,
        verbose_name="Image",
    )

    # Statut & auteur
    statut      = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default=STATUT_OUVERTE,
        verbose_name="Statut",
    )
    auteur      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="missions",
        verbose_name="Auteur",
    )

    # Timestamps
    cree_le     = models.DateTimeField(auto_now_add=True)
    modifie_le  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mission"
        verbose_name_plural = "Missions"
        ordering = ["-cree_le"]

    def __str__(self):
        return self.titre

    @property
    def nombre_candidats(self):
        return self.candidatures.count()

    @property
    def statut_badge(self):
        """Classe Bootstrap selon le statut."""
        return {
            self.STATUT_OUVERTE:  "success",
            self.STATUT_FERMEE:   "secondary",
            self.STATUT_POURVUE:  "primary",
        }.get(self.statut, "secondary")


class Candidature(models.Model):
    """Candidature d'un utilisateur à une mission."""

    STATUT_EN_ATTENTE = "attente"
    STATUT_ACCEPTEE   = "acceptee"
    STATUT_REFUSEE    = "refusee"

    STATUT_CHOICES = [
        (STATUT_EN_ATTENTE, "En attente"),
        (STATUT_ACCEPTEE,   "Acceptée"),
        (STATUT_REFUSEE,    "Refusée"),
    ]

    mission   = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="candidatures",
        verbose_name="Mission",
    )
    candidat  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidatures",
        verbose_name="Candidat",
    )
    statut    = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default=STATUT_EN_ATTENTE,
        verbose_name="Statut",
    )
    message   = models.TextField(blank=True, verbose_name="Message de motivation")
    postule_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        ordering = ["-postule_le"]
        # Un candidat ne peut postuler qu'une fois par mission
        unique_together = ("mission", "candidat")

    def __str__(self):
        return f"{self.candidat.username} → {self.mission.titre}"
