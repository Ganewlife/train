from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Media, Category, Tag, MediaView, SearchLog
from .forms import MediaUploadForm, MediaEditForm, MediaSearchForm


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def get_client_ip(request):
    """Récupère l'IP réelle du visiteur (reverse proxy compatible)."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_view(media, request):
    """Enregistre une vue unique par session."""
    session_key = f"viewed_media_{media.pk}"
    if not request.session.get(session_key):
        MediaView.objects.create(
            media=media,
            user=request.user if request.user.is_authenticated else None,
            ip_address=get_client_ip(request),
        )
        request.session[session_key] = True


def apply_search_filters(queryset, form):
    """Applique tous les filtres du formulaire de recherche."""
    data = form.cleaned_data

    # Recherche plein texte (titre, description, auteur, tags)
    q = data.get("q", "").strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(author__icontains=q)
            | Q(tags__name__icontains=q)
            | Q(category__name__icontains=q)
        ).distinct()

    if data.get("media_type"):
        queryset = queryset.filter(media_type=data["media_type"])

    if data.get("category"):
        queryset = queryset.filter(category=data["category"])

    if data.get("date_from"):
        queryset = queryset.filter(production_date__gte=data["date_from"])

    if data.get("date_to"):
        queryset = queryset.filter(production_date__lte=data["date_to"])

    if data.get("visibility"):
        queryset = queryset.filter(visibility=data["visibility"])

    # Tri
    sort = data.get("sort") or "-created_at"
    if sort == "-view_count":
        queryset = queryset.annotate(view_count=Count("views")).order_by("-view_count")
    else:
        queryset = queryset.order_by(sort)

    return queryset


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────

@login_required
def dashboard(request):
    """Tableau de bord : statistiques globales et médias récents."""
    medias = Media.objects.filter(visibility=Media.VISIBILITY_PUBLIC)

    # Statistiques
    total = medias.count()
    total_videos = medias.filter(media_type=Media.TYPE_VIDEO).count()
    total_images = medias.filter(media_type=Media.TYPE_IMAGE).count()
    total_audios = medias.filter(media_type=Media.TYPE_AUDIO).count()
    total_views = MediaView.objects.count()
    total_size = medias.aggregate(s=Sum("file_size"))["s"] or 0

    # Médias récents
    recent_medias = medias.select_related("category", "uploaded_by").prefetch_related("tags")[:8]

    # Top médias (les plus vus)
    top_medias = (
        medias.annotate(vc=Count("views"))
        .select_related("category")
        .order_by("-vc")[:5]
    )

    context = {
        "total": total,
        "total_videos": total_videos,
        "total_images": total_images,
        "total_audios": total_audios,
        "total_views": total_views,
        "total_size_gb": round(total_size / (1024 ** 3), 2),
        "recent_medias": recent_medias,
        "top_medias": top_medias,
    }
    return render(request, "greenplay/dashboard.html", context)


# ─────────────────────────────────────────────
#  CATALOGUE
# ─────────────────────────────────────────────

@login_required
def catalogue(request):
    """Liste paginée de tous les médias publics avec filtres rapides."""
    media_type = request.GET.get("type", "")
    category_slug = request.GET.get("cat", "")
    sort = request.GET.get("sort", "-created_at")

    medias = Media.objects.filter(visibility=Media.VISIBILITY_PUBLIC)

    if media_type in [Media.TYPE_VIDEO, Media.TYPE_IMAGE, Media.TYPE_AUDIO]:
        medias = medias.filter(media_type=media_type)

    if category_slug:
        medias = medias.filter(category__slug=category_slug)

    sort_options = {
        "-created_at": "-created_at",
        "created_at": "created_at",
        "title": "title",
        "-title": "-title",
    }
    medias = medias.order_by(sort_options.get(sort, "-created_at"))
    medias = medias.select_related("category", "uploaded_by").prefetch_related("tags")

    paginator = Paginator(medias, 12)
    page = paginator.get_page(request.GET.get("page"))

    categories = Category.objects.annotate(media_count=Count("medias")).filter(media_count__gt=0)

    context = {
        "page_obj": page,
        "categories": categories,
        "current_type": media_type,
        "current_cat": category_slug,
        "current_sort": sort,
        "total_count": medias.count(),
    }
    return render(request, "greenplay/catalogue.html", context)


# ─────────────────────────────────────────────
#  DÉTAIL & VISUALISATION
# ─────────────────────────────────────────────

@login_required
def media_detail(request, slug):
    """Page de visualisation d'un média + médias suggérés."""
    media = get_object_or_404(
        Media.objects.select_related("category", "uploaded_by").prefetch_related("tags"),
        slug=slug,
    )

    # Contrôle d'accès
    if media.visibility == Media.VISIBILITY_PRIVATE:
        if request.user != media.uploaded_by and not request.user.is_staff:
            return HttpResponseForbidden("Accès refusé.")

    # Enregistre la vue
    record_view(media, request)

    # Médias suggérés (même catégorie ou mêmes tags)
    suggested = (
        Media.objects.filter(
            Q(category=media.category) | Q(tags__in=media.tags.all()),
            visibility=Media.VISIBILITY_PUBLIC,
        )
        .exclude(pk=media.pk)
        .distinct()
        .annotate(vc=Count("views"))
        .order_by("-vc")[:4]
    )

    context = {
        "media": media,
        "suggested": suggested,
        "view_count": media.view_count,
    }
    return render(request, "greenplay/media_detail.html", context)


# ─────────────────────────────────────────────
#  TÉLÉVERSEMENT
# ─────────────────────────────────────────────

@login_required
def media_upload(request):
    """Formulaire de téléversement de média avec métadonnées."""
    if request.method == "POST":
        form = MediaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            media = form.save(commit=False)
            media.uploaded_by = request.user
            media.save()
            # Appel save() du form pour les tags M2M
            form.instance = media
            form.save()
            messages.success(
                request,
                f"✓ « {media.title} » a été téléversé avec succès.",
            )
            return redirect("media:detail", slug=media.slug)
    else:
        form = MediaUploadForm()

    return render(request, "greenplay/media_upload.html", {"form": form})


# ─────────────────────────────────────────────
#  ÉDITION
# ─────────────────────────────────────────────

@login_required
def media_edit(request, slug):
    """Modification des métadonnées d'un média existant."""
    media = get_object_or_404(Media, slug=slug)

    if request.user != media.uploaded_by and not request.user.is_staff:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce média.")
        return redirect("media:detail", slug=slug)

    if request.method == "POST":
        form = MediaEditForm(request.POST, request.FILES, instance=media)
        if form.is_valid():
            form.save()
            messages.success(request, f"✓ « {media.title} » a été mis à jour.")
            return redirect("media:detail", slug=media.slug)
    else:
        form = MediaEditForm(instance=media)

    return render(request, "greenplay/media_edit.html", {"form": form, "media": media})


# ─────────────────────────────────────────────
#  SUPPRESSION
# ─────────────────────────────────────────────

@login_required
@require_POST
def media_delete(request, slug):
    """Suppression sécurisée d'un média (POST uniquement)."""
    media = get_object_or_404(Media, slug=slug)

    if request.user != media.uploaded_by and not request.user.is_staff:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce média.")
        return redirect("media:detail", slug=slug)

    title = media.title
    # Supprime physiquement le fichier
    if media.file:
        try:
            media.file.delete(save=False)
        except Exception:
            pass
    if media.thumbnail:
        try:
            media.thumbnail.delete(save=False)
        except Exception:
            pass

    media.delete()
    messages.success(request, f"✓ « {title} » a été supprimé.")
    return redirect("media:catalogue")


# ─────────────────────────────────────────────
#  RECHERCHE AVANCÉE
# ─────────────────────────────────────────────

@login_required
def media_search(request):
    """Recherche avancée multi-critères avec journalisation."""
    form = MediaSearchForm(request.GET or None)
    medias = Media.objects.filter(visibility=Media.VISIBILITY_PUBLIC)
    result_count = 0

    if form.is_valid():
        medias = apply_search_filters(
            medias.select_related("category", "uploaded_by").prefetch_related("tags"),
            form,
        )
        result_count = medias.count()

        # Journalise la recherche
        q = form.cleaned_data.get("q", "")
        if q:
            SearchLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=q,
                results_count=result_count,
            )
    else:
        medias = medias.select_related("category", "uploaded_by").prefetch_related("tags")
        result_count = medias.count()

    paginator = Paginator(medias, 10)
    page = paginator.get_page(request.GET.get("page"))

    context = {
        "form": form,
        "page_obj": page,
        "result_count": result_count,
        "categories": Category.objects.all(),
        "tags": Tag.objects.annotate(mc=Count("medias")).order_by("-mc")[:20],
    }
    return render(request, "greenplay/search.html", context)


# ─────────────────────────────────────────────
#  SÉCURITÉ (admin seulement)
# ─────────────────────────────────────────────

@login_required
def security_dashboard(request):
    """Tableau de bord sécurité réservé aux administrateurs."""
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect("media:dashboard")

    from django.contrib.auth.models import User
    from django.contrib.admin.models import LogEntry

    # Statistiques de sécurité
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()

    # Derniers logs Django admin
    recent_logs = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:20]

    # Recherches récentes
    recent_searches = SearchLog.objects.select_related("user").order_by("-searched_at")[:10]

    # Médias les plus téléversés
    top_uploaders = (
        User.objects.annotate(upload_count=Count("medias"))
        .filter(upload_count__gt=0)
        .order_by("-upload_count")[:5]
    )

    context = {
        "total_users": total_users,
        "active_users": active_users,
        "staff_users": staff_users,
        "recent_logs": recent_logs,
        "recent_searches": recent_searches,
        "top_uploaders": top_uploaders,
    }
    return render(request, "greenplay/security.html", context)


# ─────────────────────────────────────────────
#  API JSON (AJAX)
# ─────────────────────────────────────────────

@login_required
def api_search(request):
    """Endpoint JSON pour la recherche instantanée (autocomplete)."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    medias = (
        Media.objects.filter(
            Q(title__icontains=q) | Q(tags__name__icontains=q),
            visibility=Media.VISIBILITY_PUBLIC,
        )
        .distinct()
        .select_related("category")[:8]
    )

    results = [
        {
            "id": m.pk,
            "title": m.title,
            "type": m.media_type,
            "type_label": m.get_media_type_display(),
            "category": m.category.name if m.category else "",
            "url": m.get_absolute_url(),
            "thumbnail": m.thumbnail.url if m.thumbnail else None,
        }
        for m in medias
    ]
    return JsonResponse({"results": results, "count": len(results)})


@login_required
@require_POST
def api_toggle_visibility(request, pk):
    """Bascule la visibilité public/privé d'un média (AJAX)."""
    media = get_object_or_404(Media, pk=pk)

    if request.user != media.uploaded_by and not request.user.is_staff:
        return JsonResponse({"error": "Non autorisé"}, status=403)

    if media.visibility == Media.VISIBILITY_PUBLIC:
        media.visibility = Media.VISIBILITY_PRIVATE
    else:
        media.visibility = Media.VISIBILITY_PUBLIC
    media.save(update_fields=["visibility"])

    return JsonResponse({
        "visibility": media.visibility,
        "label": media.get_visibility_display(),
    })
