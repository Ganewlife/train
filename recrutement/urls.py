from django.urls import path
from . import views

app_name = "recrutement"

urlpatterns = [
    # Liste & détail
    path("",                          views.liste_missions,     name="liste"),
    path("<int:pk>/",                 views.detail_mission,     name="detail"),

    # CRUD mission
    path("nouvelle/",                 views.creer_mission,      name="creer"),
    path("<int:pk>/modifier/",        views.modifier_mission,   name="modifier"),
    path("<int:pk>/supprimer/",       views.supprimer_mission,  name="supprimer"),
    path("<int:pk>/statut/",          views.changer_statut,     name="statut"),

    # Espace personnel
    path("mes-missions/",             views.mes_missions,       name="mes_missions"),
    path("mes-candidatures/",         views.mes_candidatures,   name="mes_candidatures"),
    path("candidature/<int:pk>/traiter/", views.traiter_candidature, name="traiter_candidature"),

    # Compétences (admin)
    path("competences/",              views.gerer_competences,  name="competences"),
    path("competences/<int:pk>/supprimer/", views.supprimer_competence, name="supprimer_competence"),
]
