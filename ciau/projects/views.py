import os

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    DeliverableForm,
    DeliverableUploadForm,
    LoginForm,
    PaymentCollectForm,
    PaymentForm,
    ProjectForm,
    ReferenceForm,
    WeeklyActivityForm,
)
from .models import Deliverable, Payment, Project, Reference, Stakeholder, WeeklyActivity
from .utils import get_monday, is_allowed_file, parse_monday, session_required


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login_view(request):
    if request.session.get('authenticated'):
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    error = False

    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['password'] == settings.APP_PASSWORD:
            request.session['authenticated'] = True
            return redirect('dashboard')
        error = True

    return render(request, 'login.html', {'form': form, 'error': error})


def logout_view(request):
    request.session.flush()
    return redirect('login')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@session_required
def dashboard(request):
    projects = Project.objects.exclude(etat=Project.Etat.ARCHIVE)

    etat = request.GET.get('etat')
    q    = request.GET.get('q', '').strip()

    if etat in [c[0] for c in Project.Etat.choices]:
        projects = projects.filter(etat=etat)
    if q:
        projects = projects.filter(
            designation__icontains=q
        ) | Project.objects.exclude(etat=Project.Etat.ARCHIVE).filter(
            maitre_ouvrage__icontains=q
        ) | Project.objects.exclude(etat=Project.Etat.ARCHIVE).filter(
            reference__icontains=q
        )

    today = timezone.localdate()

    nb_overdue_deliverables = Deliverable.objects.filter(
        deadline__lt=today,
        etat__in=[Deliverable.Etat.A_FAIRE, Deliverable.Etat.EN_COURS],
        project__etat__in=[Project.Etat.EN_COURS, Project.Etat.DORMANT],
    ).count()

    nb_late_payments = Payment.objects.filter(
        date_echeance__lt=today,
        date_encaissement__isnull=True,
        project__etat__in=[Project.Etat.EN_COURS, Project.Etat.DORMANT],
    ).count()

    nb_en_cours = Project.objects.filter(etat=Project.Etat.EN_COURS).count()

    return render(request, 'dashboard.html', {
        'projects': projects,
        'etat_choices': Project.Etat.choices,
        'current_etat': etat,
        'q': q,
        'nb_en_cours': nb_en_cours,
        'nb_overdue_deliverables': nb_overdue_deliverables,
        'nb_late_payments': nb_late_payments,
    })


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@session_required
def project_create(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        project = form.save()
        project_dir = settings.MEDIA_ROOT / str(project.pk)
        (project_dir / 'deliverables').mkdir(parents=True, exist_ok=True)
        (project_dir / 'references').mkdir(parents=True, exist_ok=True)
        return redirect('project_detail', pk=project.pk)

    return render(request, 'projects/form.html', {'form': form, 'action': 'Nouveau projet'})


@session_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    deliverables = sorted(project.deliverables.all(), key=lambda d: d.phase_order)
    payments     = project.payments.all()
    references   = project.references.all()

    return render(request, 'projects/detail.html', {
        'project': project,
        'deliverables': deliverables,
        'payments': payments,
        'references': references,
        'deliverable_form': DeliverableForm(),
        'payment_form': PaymentForm(),
        'reference_form': ReferenceForm(),
        'payment_collect_form': PaymentCollectForm(),
    })


@session_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('project_detail', pk=pk)

    return render(request, 'projects/form.html', {
        'form': form,
        'action': 'Modifier le projet',
        'project': project,
    })


@session_required
def project_archive(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        project.etat = Project.Etat.ARCHIVE
        project.save(update_fields=['etat', 'updated_at'])
    return redirect('dashboard')


@session_required
def project_delete(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        project.delete()
    return redirect('dashboard')


# ---------------------------------------------------------------------------
# Deliverables
# ---------------------------------------------------------------------------

@session_required
def deliverable_add(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = DeliverableForm(request.POST)
        if form.is_valid():
            deliverable = form.save(commit=False)
            deliverable.project = project
            deliverable.save()
    return redirect('project_detail', pk=pk)


@session_required
def deliverable_edit(request, pk, did):
    deliverable = get_object_or_404(Deliverable, pk=did, project_id=pk)
    if request.method == 'POST':
        form = DeliverableForm(request.POST, instance=deliverable)
        if form.is_valid():
            form.save()
    return redirect('project_detail', pk=pk)


@session_required
def deliverable_upload(request, pk, did):
    deliverable = get_object_or_404(Deliverable, pk=did, project_id=pk)
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded = request.FILES['file']
        if is_allowed_file(uploaded.name):
            if deliverable.file:
                old_path = deliverable.file.path
                if os.path.exists(old_path):
                    os.remove(old_path)
            form = DeliverableUploadForm(request.POST, request.FILES, instance=deliverable)
            if form.is_valid():
                form.save()
    return redirect('project_detail', pk=pk)


@session_required
def deliverable_delete(request, pk, did):
    if request.method == 'POST':
        deliverable = get_object_or_404(Deliverable, pk=did, project_id=pk)
        if deliverable.file:
            path = deliverable.file.path
            if os.path.exists(path):
                os.remove(path)
        deliverable.delete()
    return redirect('project_detail', pk=pk)


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@session_required
def payment_add(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.project = project
            payment.save()
    return redirect('project_detail', pk=pk)


@session_required
def payment_collect(request, pk, pid):
    payment = get_object_or_404(Payment, pk=pid, project_id=pk)
    if request.method == 'POST':
        form = PaymentCollectForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
    return redirect('project_detail', pk=pk)


@session_required
def payment_edit(request, pk, pid):
    payment = get_object_or_404(Payment, pk=pid, project_id=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
    return redirect('project_detail', pk=pk)


@session_required
def payment_delete(request, pk, pid):
    if request.method == 'POST':
        payment = get_object_or_404(Payment, pk=pid, project_id=pk)
        payment.delete()
    return redirect('project_detail', pk=pk)


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------

@session_required
def reference_add(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ReferenceForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES.get('file')
            if uploaded and not is_allowed_file(uploaded.name):
                return redirect('project_detail', pk=pk)
            ref = form.save(commit=False)
            ref.project = project
            ref.save()
    return redirect('project_detail', pk=pk)


@session_required
def reference_delete(request, pk, rid):
    if request.method == 'POST':
        ref = get_object_or_404(Reference, pk=rid, project_id=pk)
        if ref.file:
            path = ref.file.path
            if os.path.exists(path):
                os.remove(path)
        ref.delete()
    return redirect('project_detail', pk=pk)


# ---------------------------------------------------------------------------
# Weekly activities
# ---------------------------------------------------------------------------

@session_required
def activities_week(request):
    from datetime import timedelta

    semaine_str = request.GET.get('semaine')
    monday = parse_monday(semaine_str) if semaine_str else get_monday()
    friday = monday + timedelta(days=4)

    stakeholders = Stakeholder.objects.all()
    activities   = (
        WeeklyActivity.objects
        .filter(semaine_debut=monday)
        .select_related('stakeholder', 'project')
    )

    activities_by_stakeholder = {}
    for activity in activities:
        activities_by_stakeholder.setdefault(activity.stakeholder_id, []).append(activity)

    form = WeeklyActivityForm(initial={'semaine_debut': monday})

    if request.method == 'POST':
        form = WeeklyActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.semaine_debut = get_monday(activity.semaine_debut)
            activity.save()
            return redirect(f"{request.path}?semaine={monday}")

    return render(request, 'activities/week.html', {
        'monday': monday,
        'friday': friday,
        'prev_week': monday - timedelta(weeks=1),
        'next_week': monday + timedelta(weeks=1),
        'stakeholders': stakeholders,
        'activities_by_stakeholder': activities_by_stakeholder,
        'form': form,
    })


@session_required
def activity_delete(request, aid):
    if request.method == 'POST':
        activity = get_object_or_404(WeeklyActivity, pk=aid)
        monday = activity.semaine_debut
        activity.delete()
        return redirect(f"/activities/?semaine={monday}")
    return redirect('activities_week')


# ---------------------------------------------------------------------------
# Contracts & Archives
# ---------------------------------------------------------------------------

@session_required
def contracts_list(request):
    contracts = Project.objects.exclude(contrat_moe='').exclude(etat=Project.Etat.ARCHIVE)

    etat = request.GET.get('etat')
    if etat in [c[0] for c in Project.Etat.choices]:
        contracts = contracts.filter(etat=etat)

    return render(request, 'contracts/list.html', {
        'contracts': contracts,
        'etat_choices': Project.Etat.choices,
        'current_etat': etat,
    })


@session_required
def archives_list(request):
    archives = Project.objects.filter(etat=Project.Etat.ARCHIVE)
    return render(request, 'projects/archives.html', {'archives': archives})
