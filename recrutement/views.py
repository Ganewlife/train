from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Mission, Candidature, Competence
from .forms import MissionForm, CandidatureForm, CompetenceForm


# ─── LISTE DES MISSIONS ───────────────────────────────────────────────────────

@login_required
def liste_missions(request):
    """Page de consultation des missions avec nombre de candidats et statut."""
    missions = Mission.objects.prefetch_related("competences", "candidatures").select_related("auteur")

    # Filtres
    q       = request.GET.get("q", "").strip()
    statut  = request.GET.get("statut", "")
    lieu    = request.GET.get("lieu", "")

    if q:
        missions = missions.filter(
            Q(titre__icontains=q) |
            Q(description__icontains=q) |
            Q(lieu__icontains=q) |
            Q(competences__nom__icontains=q)
        ).distinct()

    if statut:
        missions = missions.filter(statut=statut)

    if lieu:
        missions = missions.filter(lieu__icontains=lieu)

    paginator = Paginator(missions, 8)
    page      = paginator.get_page(request.GET.get("page"))

    # Lieux distincts pour le filtre
    lieux = Mission.objects.values_list("lieu", flat=True).distinct().order_by("lieu")

    context = {
        "page_obj":    page,
        "total":       missions.count(),
        "q":           q,
        "statut_actif": statut,
        "lieu_actif":  lieu,
        "lieux":       lieux,
        "statuts":     Mission.STATUT_CHOICES,
    }
    return render(request, "recrutement/liste_missions.html", context)


# ─── DÉTAIL D'UNE MISSION ─────────────────────────────────────────────────────

@login_required
def detail_mission(request, pk):
    """Détail d'une mission + formulaire de candidature."""
    mission = get_object_or_404(
        Mission.objects.prefetch_related("competences", "candidatures__candidat").select_related("auteur"),
        pk=pk,
    )

    # Vérifier si l'utilisateur a déjà postulé
    deja_candidat = Candidature.objects.filter(
        mission=mission, candidat=request.user
    ).exists()

    candidature_form = None

    if request.method == "POST" and not deja_candidat and request.user != mission.auteur:
        form = CandidatureForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.mission  = mission
            c.candidat = request.user
            c.save()
            messages.success(request, "✓ Votre candidature a été envoyée avec succès.")
            return redirect("recrutement:detail", pk=pk)
        else:
            candidature_form = form
    else:
        candidature_form = CandidatureForm()

    context = {
        "mission":          mission,
        "deja_candidat":    deja_candidat,
        "candidature_form": candidature_form,
        "candidatures":     mission.candidatures.select_related("candidat").all(),
        "est_auteur":       request.user == mission.auteur,
    }
    return render(request, "recrutement/detail_mission.html", context)


# ─── CRÉER UNE MISSION ────────────────────────────────────────────────────────

@login_required
def creer_mission(request):
    """Formulaire d'enregistrement d'une nouvelle mission d'intérim."""
    if request.method == "POST":
        form = MissionForm(request.POST, request.FILES)
        if form.is_valid():
            mission        = form.save(commit=False)
            mission.auteur = request.user
            mission.save()
            form.save_m2m()  # Sauvegarder les compétences M2M
            messages.success(request, f"✓ Mission « {mission.titre} » créée avec succès.")
            return redirect("recrutement:detail", pk=mission.pk)
    else:
        form = MissionForm()

    return render(request, "recrutement/form_mission.html", {
        "form":  form,
        "titre_page": "Nouvelle mission",
        "mode": "creation",
    })


# ─── MODIFIER UNE MISSION ─────────────────────────────────────────────────────

@login_required
def modifier_mission(request, pk):
    """Modification d'une mission existante (auteur ou admin uniquement)."""
    mission = get_object_or_404(Mission, pk=pk)

    if request.user != mission.auteur and not request.user.is_staff:
        messages.error(request, "Vous n'êtes pas autorisé à modifier cette mission.")
        return redirect("recrutement:detail", pk=pk)

    if request.method == "POST":
        form = MissionForm(request.POST, request.FILES, instance=mission)
        if form.is_valid():
            form.save()
            messages.success(request, f"✓ Mission « {mission.titre} » mise à jour.")
            return redirect("recrutement:detail", pk=pk)
    else:
        form = MissionForm(instance=mission)

    return render(request, "recrutement/form_mission.html", {
        "form":       form,
        "mission":    mission,
        "titre_page": "Modifier la mission",
        "mode": "edition",
    })


# ─── SUPPRIMER UNE MISSION ────────────────────────────────────────────────────

@login_required
def supprimer_mission(request, pk):
    """Suppression d'une mission (POST uniquement)."""
    mission = get_object_or_404(Mission, pk=pk)

    if request.user != mission.auteur and not request.user.is_staff:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer cette mission.")
        return redirect("recrutement:detail", pk=pk)

    if request.method == "POST":
        titre = mission.titre
        mission.delete()
        messages.success(request, f"✓ Mission « {titre} » supprimée.")
        return redirect("recrutement:liste")

    return render(request, "recrutement/confirmer_suppression.html", {"mission": mission})


# ─── CHANGER LE STATUT ────────────────────────────────────────────────────────

@login_required
def changer_statut(request, pk):
    """Changer le statut d'une mission (ouverte / fermée / pourvue)."""
    mission = get_object_or_404(Mission, pk=pk)

    if request.user != mission.auteur and not request.user.is_staff:
        messages.error(request, "Action non autorisée.")
        return redirect("recrutement:detail", pk=pk)

    if request.method == "POST":
        nouveau_statut = request.POST.get("statut")
        if nouveau_statut in dict(Mission.STATUT_CHOICES):
            mission.statut = nouveau_statut
            mission.save(update_fields=["statut"])
            messages.success(request, f"Statut mis à jour : {mission.get_statut_display()}")

    return redirect("recrutement:detail", pk=pk)


# ─── MES MISSIONS (auteur) ────────────────────────────────────────────────────

@login_required
def mes_missions(request):
    """Missions créées par l'utilisateur connecté."""
    missions = Mission.objects.filter(auteur=request.user).prefetch_related("candidatures")
    return render(request, "recrutement/mes_missions.html", {"missions": missions})


# ─── MES CANDIDATURES ─────────────────────────────────────────────────────────

@login_required
def mes_candidatures(request):
    """Candidatures soumises par l'utilisateur connecté."""
    candidatures = Candidature.objects.filter(
        candidat=request.user
    ).select_related("mission", "mission__auteur")
    return render(request, "recrutement/mes_candidatures.html", {"candidatures": candidatures})


# ─── GESTION DES COMPÉTENCES ─────────────────────────────────────────────────

@login_required
def gerer_competences(request):
    """Ajouter / supprimer des compétences du répertoire (staff uniquement)."""
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect("recrutement:liste")

    if request.method == "POST":
        form = CompetenceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✓ Compétence ajoutée.")
            return redirect("recrutement:competences")
    else:
        form = CompetenceForm()

    competences = Competence.objects.all()
    return render(request, "recrutement/competences.html", {
        "form": form,
        "competences": competences,
    })


@login_required
def supprimer_competence(request, pk):
    """Suppression d'une compétence (staff uniquement, POST)."""
    if not request.user.is_staff:
        return redirect("recrutement:liste")
    competence = get_object_or_404(Competence, pk=pk)
    if request.method == "POST":
        competence.delete()
        messages.success(request, "Compétence supprimée.")
    return redirect("recrutement:competences")


@login_required
def traiter_candidature(request, pk):
    candidature = get_object_or_404(Candidature, pk=pk)
    
    if request.user != candidature.mission.auteur:
        messages.error(request, "Non autorisé.")
        return redirect("recrutement:detail", pk=candidature.mission.pk)

    if request.method == "POST":
        nouveau_statut = request.POST.get("statut")
        if nouveau_statut in ["acceptee", "refusee", "attente"]:
            candidature.statut = nouveau_statut
            candidature.save(update_fields=["statut"])
            messages.success(request, "Candidature mise à jour.")

    return redirect("recrutement:detail", pk=candidature.mission.pk)