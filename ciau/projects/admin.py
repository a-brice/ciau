from django.contrib import admin

from .models import Deliverable, Payment, Project, Reference, Stakeholder, WeeklyActivity


@admin.register(Stakeholder)
class StakeholderAdmin(admin.ModelAdmin):
    list_display = ['nom', 'poste']
    search_fields = ['nom', 'poste']


class DeliverableInline(admin.TabularInline):
    model = Deliverable
    extra = 0
    fields = ['phase', 'etat', 'deadline', 'commentaire']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['numero', 'declenchement', 'montant', 'date_echeance', 'date_encaissement']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display    = ['reference', 'designation', 'maitre_ouvrage', 'etat', 'phase_actuelle', 'honoraires', 'potentiel']
    list_filter     = ['etat', 'contrat_moe', 'potentiel', 'phase_actuelle']
    search_fields   = ['reference', 'designation', 'maitre_ouvrage']
    inlines         = [DeliverableInline, PaymentInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Deliverable)
class DeliverableAdmin(admin.ModelAdmin):
    list_display  = ['project', 'phase', 'etat', 'deadline']
    list_filter   = ['phase', 'etat']
    search_fields = ['project__reference', 'project__designation']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['project', 'numero', 'montant', 'date_echeance', 'date_encaissement']
    list_filter   = ['date_encaissement']
    search_fields = ['project__reference', 'declenchement']


@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display  = ['project', 'type', 'libelle', 'valeur']
    list_filter   = ['type']
    search_fields = ['project__reference', 'libelle']


@admin.register(WeeklyActivity)
class WeeklyActivityAdmin(admin.ModelAdmin):
    list_display  = ['stakeholder', 'project', 'semaine_debut', 'delai']
    list_filter   = ['semaine_debut', 'stakeholder']
    search_fields = ['stakeholder__nom', 'activite']
