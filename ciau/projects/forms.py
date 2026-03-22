from django import forms

from .models import Deliverable, Payment, Project, Reference, Stakeholder, WeeklyActivity


class LoginForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autofocus': True, 'placeholder': 'Mot de passe'}),
        label='Mot de passe',
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'reference', 'designation', 'maitre_ouvrage', 'description',
            'responsable_etudes', 'consultant_ext', 'contrat_moe',
            'etat', 'phase_actuelle', 'potentiel', 'honoraires',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class DeliverableForm(forms.ModelForm):
    class Meta:
        model = Deliverable
        fields = ['phase', 'etat', 'commentaire', 'deadline']
        widgets = {
            'commentaire': forms.Textarea(attrs={'rows': 2}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }


class DeliverableUploadForm(forms.ModelForm):
    class Meta:
        model = Deliverable
        fields = ['file']


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['numero', 'declenchement', 'montant', 'date_echeance']
        widgets = {
            'declenchement': forms.Textarea(attrs={'rows': 2}),
            'date_echeance': forms.DateInput(attrs={'type': 'date'}),
        }


class PaymentCollectForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['date_encaissement']
        widgets = {
            'date_encaissement': forms.DateInput(attrs={'type': 'date'}),
        }


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = ['type', 'libelle', 'valeur', 'file']


class WeeklyActivityForm(forms.ModelForm):
    class Meta:
        model = WeeklyActivity
        fields = ['stakeholder', 'project', 'semaine_debut', 'activite', 'delai', 'observations']
        widgets = {
            'semaine_debut': forms.DateInput(attrs={'type': 'date'}),
            'activite': forms.Textarea(attrs={'rows': 2}),
            'observations': forms.Textarea(attrs={'rows': 2}),
            'delai': forms.DateInput(attrs={'type': 'date'}),
        }
