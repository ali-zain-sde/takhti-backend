from django.contrib import admin

from apps.tenancy.models import Campus, Organisation


class CampusInline(admin.TabularInline[Campus, Organisation]):
    model = Campus
    fields = ("name", "slug", "province", "city", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    extra = 0


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin[Organisation]):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = (CampusInline,)


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin[Campus]):
    list_display = ("name", "organisation", "province", "city", "is_active")
    list_filter = ("province", "is_active")
    search_fields = ("name", "slug", "city", "organisation__name")
    list_select_related = ("organisation",)
    autocomplete_fields = ("organisation",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "created_at", "updated_at")
