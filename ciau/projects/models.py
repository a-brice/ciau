from django.db import models
from django.utils import timezone

from .utils import deliverable_upload_to, reference_upload_to


class Stakeholder(models.Model):
    nom = models.CharField(max_length=200)
    poste = models.CharField(max_length=200)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Intervenant'
        verbose_name_plural = 'Intervenants'

    def __str__(self):
        return f"{self.nom} — {self.poste}"


class Project(models.Model):

    class Etat(models.TextChoices):
        EN_COURS = 'en_cours', 'En cours'
        DORMANT  = 'dormant',  'Dormant'
        ARCHIVE  = 'archive',  'Archivé'

    class ContratMoe(models.TextChoices):
        SIGNE      = 'signe',      'Signé et en suivi'
        PROJET     = 'projet',     'Projet de contrat'
        A_VERIFIER = 'a_verifier', 'Contrat à vérifier'

    class Phase(models.TextChoices):
        EP      = 'EP',      'Études Préliminaires'
        APS     = 'APS',     'Avant-Projet Sommaire'
        APD     = 'APD',     'Avant-Projet Détaillé'
        IPC     = 'IPC',     'Instruction du Permis de Construire'
        PCG     = 'PCG',     'Projet de Conception Général'
        DCE     = 'DCE',     'Dossier de Consultation des Entreprises'
        MDT     = 'MDT',     'Mise au Point des Marchés de Travaux'
        TRAVAUX = 'TRAVAUX', 'Travaux'

    reference          = models.CharField(max_length=100)
    designation        = models.CharField(max_length=300)
    maitre_ouvrage     = models.CharField(max_length=200, blank=True)
    description        = models.TextField(blank=True)
    responsable_etudes = models.CharField(max_length=200, blank=True)
    consultant_ext     = models.CharField(max_length=200, blank=True)
    contrat_moe        = models.CharField(max_length=20, choices=ContratMoe.choices, blank=True)
    etat               = models.CharField(max_length=20, choices=Etat.choices, default=Etat.EN_COURS)
    phase_actuelle     = models.CharField(max_length=20, choices=Phase.choices, blank=True)
    potentiel          = models.BooleanField(default=False)
    honoraires         = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Projet'
        verbose_name_plural = 'Projets'

    def __str__(self):
        return f"{self.reference} — {self.designation}"

    # --- Computed financials ---

    @property
    def total_encaisse(self):
        result = self.payments.filter(
            date_encaissement__isnull=False
        ).aggregate(total=models.Sum('montant'))['total']
        return result or 0

    @property
    def solde(self):
        """Remaining to collect: honoraires - total received. Negative = overpaid."""
        if self.honoraires is None:
            return None
        return self.honoraires - self.total_encaisse

    # --- Computed progress ---

    @property
    def progression(self):
        """Percentage of deliverables in 'valide' state."""
        total = self.deliverables.count()
        if total == 0:
            return 0
        validated = self.deliverables.filter(etat=Deliverable.Etat.VALIDE).count()
        return round((validated / total) * 100)

    # --- Alert flags (used in dashboard) ---

    @property
    def has_overdue_deliverables(self):
        today = timezone.localdate()
        return self.deliverables.filter(
            deadline__lt=today,
            etat__in=[Deliverable.Etat.A_FAIRE, Deliverable.Etat.EN_COURS],
        ).exists()

    @property
    def has_late_payments(self):
        today = timezone.localdate()
        return self.payments.filter(
            date_echeance__lt=today,
            date_encaissement__isnull=True,
        ).exists()


class Deliverable(models.Model):

    PHASE_ORDER = ['EP', 'APS', 'APD', 'IPC', 'PCG', 'DCE', 'MDT', 'TRAVAUX']

    class Phase(models.TextChoices):
        EP      = 'EP',      'Études Préliminaires'
        APS     = 'APS',     'Avant-Projet Sommaire'
        APD     = 'APD',     'Avant-Projet Détaillé'
        IPC     = 'IPC',     'Instruction du Permis de Construire'
        PCG     = 'PCG',     'Projet de Conception Général'
        DCE     = 'DCE',     'Dossier de Consultation des Entreprises'
        MDT     = 'MDT',     'Mise au Point des Marchés de Travaux'
        TRAVAUX = 'TRAVAUX', 'Travaux'

    class Etat(models.TextChoices):
        A_FAIRE  = 'a_faire',  'À faire'
        EN_COURS = 'en_cours', 'En cours'
        LIVRE    = 'livre',    'Livré'
        VALIDE   = 'valide',   'Validé'

    project     = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='deliverables')
    phase       = models.CharField(max_length=20, choices=Phase.choices)
    etat        = models.CharField(max_length=20, choices=Etat.choices, default=Etat.A_FAIRE)
    commentaire = models.TextField(blank=True)
    deadline    = models.DateField(null=True, blank=True)
    file        = models.FileField(upload_to=deliverable_upload_to, null=True, blank=True)

    class Meta:
        verbose_name = 'Livrable'
        verbose_name_plural = 'Livrables'

    def __str__(self):
        return f"{self.project.reference} — {self.phase}"

    @property
    def phase_order(self):
        """Integer position in PHASE_ORDER, used for sorting."""
        try:
            return self.PHASE_ORDER.index(self.phase)
        except ValueError:
            return 99

    @property
    def is_overdue(self):
        if self.deadline and self.etat in [self.Etat.A_FAIRE, self.Etat.EN_COURS]:
            return self.deadline < timezone.localdate()
        return False

    @property
    def is_urgent(self):
        """Deadline within 7 days and not yet validated."""
        if self.deadline and self.etat in [self.Etat.A_FAIRE, self.Etat.EN_COURS]:
            delta = self.deadline - timezone.localdate()
            return 0 <= delta.days <= 7
        return False


class Payment(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        RECU       = 'recu',       'Reçu'
        EN_RETARD  = 'en_retard',  'En retard'

    project          = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payments')
    numero           = models.PositiveIntegerField()
    declenchement    = models.TextField(blank=True)
    montant          = models.DecimalField(max_digits=15, decimal_places=0)
    date_echeance    = models.DateField(null=True, blank=True)
    date_encaissement = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['numero']
        verbose_name = 'Acompte'
        verbose_name_plural = 'Acomptes'

    def __str__(self):
        return f"{self.project.reference} — Acompte {self.numero}"

    @property
    def statut(self):
        if self.date_encaissement:
            return self.Statut.RECU
        if self.date_echeance and self.date_echeance < timezone.localdate():
            return self.Statut.EN_RETARD
        return self.Statut.EN_ATTENTE


class Reference(models.Model):

    class Type(models.TextChoices):
        DOCUMENT = 'document', 'Document'
        LIEN     = 'lien',     'Lien'
        CONTACT  = 'contact',  'Contact'
        AUTRE    = 'autre',    'Autre'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='references')
    type    = models.CharField(max_length=20, choices=Type.choices, default=Type.DOCUMENT)
    libelle = models.CharField(max_length=200)
    valeur  = models.CharField(max_length=500, blank=True)
    file    = models.FileField(upload_to=reference_upload_to, null=True, blank=True)

    class Meta:
        ordering = ['type', 'libelle']
        verbose_name = 'Référence'
        verbose_name_plural = 'Références'

    def __str__(self):
        return f"{self.project.reference} — {self.libelle}"


class WeeklyActivity(models.Model):
    stakeholder  = models.ForeignKey(Stakeholder, on_delete=models.CASCADE, related_name='activities')
    project      = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    semaine_debut = models.DateField()  # Always a Monday
    activite     = models.TextField()
    delai        = models.DateField(null=True, blank=True)
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ['semaine_debut', 'stakeholder']
        verbose_name = 'Activité hebdomadaire'
        verbose_name_plural = 'Activités hebdomadaires'

    def __str__(self):
        return f"{self.stakeholder.nom} — semaine du {self.semaine_debut}"
