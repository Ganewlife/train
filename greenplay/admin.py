from django.contrib import admin
from .models import Media, Category, Tag, MediaView, SearchLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


class MediaViewInline(admin.TabularInline):
    model = MediaView
    extra = 0
    readonly_fields = ["user", "ip_address", "viewed_at"]
    can_delete = False


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = [
        "title", "media_type", "category", "visibility",
        "uploaded_by", "view_count", "created_at",
    ]
    list_filter = ["media_type", "visibility", "category", "license"]
    search_fields = ["title", "description", "author", "tags__name"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["slug", "file_size", "created_at", "updated_at", "view_count"]
    filter_horizontal = ["tags"]
    raw_id_fields = ["uploaded_by"]
    inlines = [MediaViewInline]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Informations principales", {
            "fields": ("title", "slug", "media_type", "description")
        }),
        ("Fichiers", {
            "fields": ("file", "thumbnail", "file_size", "duration")
        }),
        ("Métadonnées", {
            "fields": ("category", "tags", "author", "production_date")
        }),
        ("Accès & Licence", {
            "fields": ("visibility", "license", "uploaded_by")
        }),
        ("Dates", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def view_count(self, obj):
        return obj.view_count
    view_count.short_description = "Vues"


@admin.register(MediaView)
class MediaViewAdmin(admin.ModelAdmin):
    list_display = ["media", "user", "ip_address", "viewed_at"]
    list_filter = ["viewed_at"]
    readonly_fields = ["media", "user", "ip_address", "viewed_at"]


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ["query", "user", "results_count", "searched_at"]
    readonly_fields = ["query", "user", "results_count", "searched_at"]
    list_filter = ["searched_at"]
