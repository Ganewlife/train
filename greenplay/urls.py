from django.urls import path
from greenplay import views as play_views

app_name = "media"

urlpatterns = [
    # Dashboard
    path("", play_views.dashboard, name="dashboard"),

    # Catalogue
    path("catalogue/", play_views.catalogue, name="catalogue"),

    # Recherche
    path("recherche/", play_views.media_search, name="search"),

    # Téléversement
    path("upload/", play_views.media_upload, name="upload"),

    # Détail / visualisation
    path("media/<slug:slug>/", play_views.media_detail, name="detail"),

    # Édition
    path("media/<slug:slug>/editer/", play_views.media_edit, name="edit"),

    # Suppression
    path("media/<slug:slug>/supprimer/", play_views.media_delete, name="delete"),

    # Sécurité (admin)
    path("securite/", play_views.security_dashboard, name="security"),

    # API JSON
    path("api/search/", play_views.api_search, name="api_search"),
    path("api/media/<int:pk>/visibilite/", play_views.api_toggle_visibility, name="api_toggle_visibility"),
]
