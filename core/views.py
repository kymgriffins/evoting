# views.py — ALL the brains of this app.
# Every page request hits a function here.
# URLs → Views → Models → Templates (or JSON for APIs)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages  # Flash messages (success/error popups)
from django.db import models, transaction
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status  # Django REST Framework
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import User, Election, Position, Candidate, Manifesto, Vote, ManifestoUpdate, ManifestoRating, AuditLog, Category
from .forms import (UserRegisterForm, CandidateForm, ManifestoForm,
                    ManifestoUpdateForm, ManifestoRatingForm, ElectionForm, PositionForm)
from .serializers import (UserSerializer, ElectionSerializer, PositionSerializer,
                          CandidateSerializer, ManifestoSerializer, VoteSerializer,
                          ManifestoUpdateSerializer, ManifestoRatingSerializer, AuditLogSerializer,
                          CategorySerializer)


# ─── HELPER FUNCTIONS ────────────────────────────────────────

def log_audit(user, action, details='', request=None):
    """Record every important action in the AuditLog table.
    This is our 'blockchain' — every vote, approval, and registration
    is logged with user, action, IP address, and timestamp."""
    ip = request.META.get('REMOTE_ADDR') if request else None
    AuditLog.objects.create(user=user, action=action, details=details, ip_address=ip)


def is_admin(user):
    """Check if a user is an admin — used by @user_passes_test decorator"""
    return user.is_authenticated and user.role == 'admin'

def is_candidate(user):
    return user.is_authenticated and user.role == 'candidate'


# ─── PUBLIC PAGES (no login required) ────────────────────────

def documentation(request):
    """Comprehensive documentation page — explains models, views, templates,
    migrations, testing, and provides external learning resources."""
    return render(request, 'core/documentation.html')


def home(request):
    """Landing page — shows active elections to everyone"""
    active_elections = Election.objects.filter(is_active=True, end_date__gte=timezone.now())
    return render(request, 'core/home.html', {'elections': active_elections})


def register(request):
    """User registration — creates account with role (voter or candidate).
    Uses Django's built-in UserCreationForm extended with our custom fields."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()          # Creates the User in database
            login(request, user)        # Logs them in immediately
            log_audit(user, f'User registered as {user.role}', request=request)
            messages.success(request, 'Registration successful!')
            if user.role == 'candidate':
                return redirect('candidate_setup')  # Candidates must set up profile
            return redirect('dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def results(request, election_id=None):
    """Public election results page — shows vote counts per candidate.
    If election_id is given, shows that election. Otherwise shows all past elections.
    Candidates must opt-in to view all results (requirement 6)."""
    if election_id:
        elections = Election.objects.filter(id=election_id)
    else:
        elections = Election.objects.filter(end_date__lt=timezone.now())

    is_candidate = request.user.is_authenticated and request.user.role == 'candidate'
    view_all = request.GET.get('view_all') == '1'

    if is_candidate and not view_all:
        try:
            my_profile = request.user.candidate_profile
            my_election_id = my_profile.election_id
            results_data = []
            for election in elections:
                if election.id != my_election_id and election.id != request.GET.get('election_id'):
                    continue
                positions_data = []
                for position in election.positions.all():
                    candidates = Candidate.objects.filter(position=position, is_approved=True)
                    candidate_data = []
                    for c in candidates:
                        vote_count = Vote.objects.filter(candidate=c, election=election).count()
                        candidate_data.append({'candidate': c, 'vote_count': vote_count})
                    candidate_data.sort(key=lambda x: x['vote_count'], reverse=True)
                    positions_data.append({'position': position, 'candidates': candidate_data})
                results_data.append({'election': election, 'positions': positions_data})
            return render(request, 'core/results.html', {
                'results': results_data,
                'is_candidate': True,
                'view_all': False,
                'my_election_id': my_election_id,
            })
        except Candidate.DoesNotExist:
            pass

    results_data = []
    for election in elections:
        positions_data = []
        for position in election.positions.all():
            candidates = Candidate.objects.filter(position=position, is_approved=True)
            candidate_data = []
            for c in candidates:
                vote_count = Vote.objects.filter(candidate=c, election=election).count()
                candidate_data.append({'candidate': c, 'vote_count': vote_count})
            candidate_data.sort(key=lambda x: x['vote_count'], reverse=True)
            positions_data.append({'position': position, 'candidates': candidate_data})
        results_data.append({'election': election, 'positions': positions_data})

    return render(request, 'core/results.html', {
        'results': results_data,
        'is_candidate': is_candidate,
        'view_all': True,
    })


def manifesto_tracking(request, election_id=None):
    """Public manifesto tracking dashboard.
    Shows every candidate's promises with their current progress status,
    average ratings, and rating counts. Voters can rate from here."""
    if election_id:
        elections = Election.objects.filter(id=election_id)
    else:
        elections = Election.objects.all()

    tracking_data = []
    for election in elections:
        candidates = Candidate.objects.filter(election=election, is_approved=True)
        candidates_data = []
        for c in candidates:
            manifestos = Manifesto.objects.filter(candidate=c)
            manifestos_data = []
            for m in manifestos:
                latest_update = ManifestoUpdate.objects.filter(manifesto=m).first()
                avg_rating = ManifestoRating.objects.filter(manifesto=m).aggregate(
                    avg=models.Avg('rating')
                )['avg']
                rating_count = ManifestoRating.objects.filter(manifesto=m).count()
                manifestos_data.append({
                    'manifesto': m,
                    'latest_status': latest_update.get_status_display() if latest_update else 'No Updates',
                    'updates_count': ManifestoUpdate.objects.filter(manifesto=m).count(),
                    'avg_rating': round(avg_rating, 1) if avg_rating else 0,
                    'rating_count': rating_count,
                })
            candidates_data.append({'candidate': c, 'manifestos': manifestos_data})
        tracking_data.append({'election': election, 'candidates': candidates_data})

    return render(request, 'core/manifesto_tracking.html', {'tracking_data': tracking_data})


def leaderboard(request):
    """Public leaderboard — ranks candidates by average rating.
    Removed success rate and vote counts — only rating matters."""
    candidates = Candidate.objects.filter(is_approved=True).select_related('user', 'position', 'election')
    ranking = []
    for c in candidates:
        avg_rating = ManifestoRating.objects.filter(manifesto__candidate=c).aggregate(
            avg=models.Avg('rating')
        )['avg']
        rating_count = ManifestoRating.objects.filter(manifesto__candidate=c).count()

        ranking.append({
            'candidate': c,
            'avg_rating': round(avg_rating, 1) if avg_rating else 0,
            'rating_count': rating_count,
        })

    ranking.sort(key=lambda x: x['avg_rating'], reverse=True)
    for idx, r in enumerate(ranking, 1):
        r['rank'] = idx

    return render(request, 'core/leaderboard.html', {'ranking': ranking})


# ─── AUTHENTICATED PAGES (must be logged in) ─────────────────

@login_required
def dashboard(request):
    """Role-based dashboard — shows DIFFERENT content for admin/voter/candidate.
    - Admin: system stats, election history, audit log link
    - Candidate: their profile, manifestos with latest status
    - Voter: active elections, past voting history"""
    user = request.user
    active_elections = Election.objects.filter(is_active=True)
    past_elections = Election.objects.filter(end_date__lt=timezone.now())
    all_elections = Election.objects.all().order_by('-start_date')

    if user.role == 'admin':
        total_voters = User.objects.filter(role='voter').count()
        total_candidates_count = Candidate.objects.filter(is_approved=True).count()
        total_votes = Vote.objects.count()
        pending_candidates = Candidate.objects.filter(is_approved=False).count()
        total_manifestos = Manifesto.objects.count()
        total_updates = ManifestoUpdate.objects.count()
        voter_turnout = round((total_votes / (total_voters * max(len(all_elections), 1))) * 100, 1) if total_voters > 0 else 0

        election_stats = []
        for e in all_elections:
            vc = Vote.objects.filter(election=e).count()
            cc = Candidate.objects.filter(election=e, is_approved=True).count()
            mc = Manifesto.objects.filter(candidate__election=e).count()
            pos_count = e.positions.count()
            eligible_positions = pos_count if pos_count > 0 else 1
            e_turnout = round((vc / (total_voters * eligible_positions)) * 100, 1) if total_voters > 0 else 0
            election_stats.append({'election': e, 'votes': vc, 'candidates': cc, 'manifestos': mc, 'turnout': e_turnout})

        return render(request, 'core/dashboard.html', {
            'section': 'admin', 'now': timezone.now(),
            'total_voters': total_voters, 'total_candidates': total_candidates_count,
            'total_votes': total_votes, 'pending_candidates': pending_candidates,
            'total_manifestos': total_manifestos, 'total_updates': total_updates,
            'active_elections': active_elections, 'past_elections': past_elections,
            'all_elections': all_elections, 'election_stats': election_stats,
            'voter_turnout': voter_turnout,
        })

    elif user.role == 'candidate':
        try:
            candidate = user.candidate_profile
        except Candidate.DoesNotExist:
            return redirect('candidate_setup')
        my_manifestos = Manifesto.objects.filter(candidate=candidate).prefetch_related('updates', 'categories')
        return render(request, 'core/dashboard.html', {
            'section': 'candidate', 'candidate': candidate,
            'manifestos': my_manifestos, 'active_elections': active_elections,
        })

    else:  # voter
        has_voted_positions = Vote.objects.filter(voter=user).values_list('position_id', flat=True)
        voted_election_ids = Vote.objects.filter(voter=user).values_list('election_id', flat=True).distinct()
        return render(request, 'core/dashboard.html', {
            'section': 'voter', 'now': timezone.now(),
            'active_elections': active_elections, 'past_elections': past_elections,
            'has_voted_positions': list(has_voted_positions),
            'voted_election_ids': list(voted_election_ids),
        })


# ─── CANDIDATE SETUP ─────────────────────────────────────────

@login_required
def candidate_setup(request):
    """First-time setup for candidates after registration.
    They pick their election, position, and write a bio.
    Candidate requests to be vetted — admin must approve."""
    if request.user.role != 'candidate':
        messages.error(request, 'You must register as a candidate first.')
        return redirect('register')

    existing = Candidate.objects.filter(user=request.user).first()
    if existing:
        if existing.approval_status == 'rejected':
            messages.info(request, 'Your previous request was rejected. You can submit a new request.')
            existing.delete()
        else:
            return redirect('dashboard')

    all_elections = Election.objects.all()
    positions = Position.objects.all()
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            election_id = request.POST.get('election')
            position = form.cleaned_data['position']
            if not election_id:
                messages.error(request, 'Please select an election.')
                return render(request, 'core/candidate_setup.html', {
                    'form': form, 'elections': all_elections, 'positions': positions,
                })
            if str(position.election_id) != election_id:
                messages.error(request, 'Selected position does not belong to the chosen election.')
                return render(request, 'core/candidate_setup.html', {
                    'form': form, 'elections': all_elections, 'positions': positions,
                })
            candidate = form.save(commit=False)
            candidate.user = request.user
            candidate.election_id = election_id
            candidate.approval_status = 'pending'
            candidate.save()
            log_audit(request.user, 'Candidate profile created — vetting requested', request=request)
            messages.success(request, 'Vetting request submitted! Awaiting admin approval.')
            return redirect('dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CandidateForm()

    return render(request, 'core/candidate_setup.html', {
        'form': form, 'elections': all_elections, 'positions': positions,
    })


# ─── MANIFESTO CRUD (Candidates manage their promises) ───────

@login_required
def manage_manifestos(request):
    """Lists all manifestos for the logged-in candidate"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'Complete your candidate profile first.')
        return redirect('candidate_setup')

    if not candidate.is_approved:
        messages.warning(request, 'Your candidate profile is pending approval.')
        return redirect('dashboard')

    manifestos = Manifesto.objects.filter(candidate=candidate).prefetch_related('updates', 'categories')
    return render(request, 'core/manifesto_list.html', {
        'manifestos': manifestos, 'candidate': candidate,
    })


@login_required
def manifesto_create(request):
    """Create a new manifesto (campaign promise)"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        return redirect('candidate_setup')
    if not candidate.is_approved:
        messages.warning(request, 'Your profile is not yet approved.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ManifestoForm(request.POST)
        if form.is_valid():
            manifesto = form.save(commit=False)
            manifesto.candidate = candidate
            manifesto.save()
            form.save_m2m()
            log_audit(request.user, f'Manifesto created: {manifesto.title}', request=request)
            messages.success(request, 'Manifesto item added!')
            return redirect('manage_manifestos')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ManifestoForm()
    return render(request, 'core/manifesto_form.html', {'form': form})


@login_required
def manifesto_updates(request, manifesto_pk):
    """View a single manifesto's detail page.
    Shows progress updates, user ratings & comments, and allows
    candidates to add updates or voters to rate."""
    manifesto = get_object_or_404(Manifesto, pk=manifesto_pk)
    updates = ManifestoUpdate.objects.filter(manifesto=manifesto)

    if request.method == 'POST':
        form = ManifestoUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.manifesto = manifesto
            update.save()
            log_audit(request.user, f'Manifesto update: {manifesto.title}', request=request)
            messages.success(request, 'Update posted!')
            return redirect('manifesto_updates', manifesto_pk=manifesto.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ManifestoUpdateForm()

    ratings = ManifestoRating.objects.filter(manifesto=manifesto).select_related('user')
    return render(request, 'core/manifesto_updates.html', {
        'manifesto': manifesto, 'updates': updates,
        'ratings': ratings, 'form': form,
    })


# ─── VOTING ──────────────────────────────────────────────────

@login_required
def vote_page(request, election_id):
    """Ballot page. Shows all positions with candidates.
    Prevents double voting via unique_together constraint.
    Only available for active elections that haven't ended."""
    election = get_object_or_404(Election, id=election_id, is_active=True)
    if timezone.now() > election.end_date:
        messages.error(request, 'This election has ended.')
        return redirect('dashboard')

    if request.method == 'POST':
        # Iterate each position and save the vote
        for position in election.positions.all():
            candidate_id = request.POST.get(f'position_{position.id}')
            if candidate_id:
                candidate = get_object_or_404(Candidate, id=candidate_id)
                # Check prevents duplicate (though DB also enforces this)
                if not Vote.objects.filter(voter=request.user, position=position, election=election).exists():
                    Vote.objects.create(
                        voter=request.user, candidate=candidate,
                        position=position, election=election,
                    )
                    log_audit(request.user, f'Voted for {candidate} in {position}', request=request)
        messages.success(request, 'Your votes have been cast successfully!')
        return redirect('dashboard')

    positions = election.positions.all()
    voted_positions = Vote.objects.filter(voter=request.user, election=election).values_list('position_id', flat=True)

    for pos in positions:
        pos.candidate_list = Candidate.objects.filter(position=pos, is_approved=True)
        pos.has_voted = pos.id in voted_positions

    return render(request, 'core/vote.html', {
        'election': election, 'positions': positions,
    })


# ─── MANIFESTO RATING ────────────────────────────────────────

@login_required
def rate_manifesto(request, manifesto_pk):
    """Handle manifesto rating form submission.
    Voters rate 1-5 stars and optionally leave a comment.
    If they already rated, it updates their previous rating."""
    manifesto = get_object_or_404(Manifesto, pk=manifesto_pk)
    existing = ManifestoRating.objects.filter(user=request.user, manifesto=manifesto).first()

    if request.method == 'POST':
        form = ManifestoRatingForm(request.POST, instance=existing)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.manifesto = manifesto
            rating.save()
            log_audit(request.user, f'Rated manifesto: {manifesto.title}', request=request)
            messages.success(request, 'Your rating has been submitted!')
        else:
            messages.error(request, 'Please select a rating.')
        return redirect('manifesto_tracking')

    return redirect('manifesto_tracking')


# ─── ADMIN PAGES ─────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_elections(request):
    """Admin: Create and list elections"""
    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            election = form.save()
            clone_id = request.POST.get('clone_from')
            if clone_id:
                source = get_object_or_404(Election, id=clone_id)
                for pos in source.positions.all():
                    Position.objects.create(
                        election=election,
                        title=pos.title,
                        description=pos.description,
                        order=pos.order,
                    )
                log_audit(request.user, f'Election created (cloned {source.id} positions)', request=request)
                messages.success(request, f'Election created with positions from "{source.title}"!')
            else:
                log_audit(request.user, 'Election created', request=request)
                messages.success(request, 'Election created!')
            return redirect('admin_elections')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ElectionForm()

    elections = Election.objects.all()
    now = timezone.now()
    election_data = []
    active_count = 0
    inactive_count = 0
    past_count = 0
    for e in elections:
        approved_count = Candidate.objects.filter(election=e, is_approved=True).count()
        election_data.append({'election': e, 'approved_count': approved_count})
        if e.end_date < now:
            past_count += 1
        elif e.is_active:
            active_count += 1
        else:
            inactive_count += 1
    return render(request, 'core/admin_elections.html', {
        'form': form, 'elections': elections, 'election_data': election_data, 'now': now,
        'active_count': active_count, 'inactive_count': inactive_count, 'past_count': past_count,
    })


@login_required
@user_passes_test(is_admin)
def admin_election_edit(request, pk):
    """Admin: Edit an existing election"""
    election = get_object_or_404(Election, pk=pk)
    if request.method == 'POST':
        form = ElectionForm(request.POST, instance=election)
        if form.is_valid():
            form.save()
            messages.success(request, 'Election updated!')
            return redirect('admin_elections')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ElectionForm(instance=election)
    elections = Election.objects.all()
    election_data = []
    for e in elections:
        approved_count = Candidate.objects.filter(election=e, is_approved=True).count()
        election_data.append({'election': e, 'approved_count': approved_count})
    return render(request, 'core/admin_elections.html', {
        'form': form, 'editing': True, 'elections': elections, 'election_data': election_data, 'now': timezone.now(),
    })


@login_required
@user_passes_test(is_admin)
def admin_positions(request, election_id):
    """Admin: Add positions to an election (President, VP, etc.)"""
    election = get_object_or_404(Election, id=election_id)
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            position = form.save(commit=False)
            position.election = election
            position.save()
            messages.success(request, 'Position added!')
            return redirect('admin_positions', election_id=election.id)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = PositionForm()

    positions = Position.objects.filter(election=election)
    return render(request, 'core/admin_positions.html', {
        'form': form, 'election': election, 'positions': positions,
    })


@login_required
@user_passes_test(is_admin)
def admin_election_activate(request, pk):
    """Admin: Activate an election — only if end_date is in the future"""
    election = get_object_or_404(Election, pk=pk)
    now = timezone.now()
    if election.end_date < now:
        messages.error(request, f'Cannot activate "{election.title}" — its end date ({election.end_date.strftime("%b %d, %Y %H:%M")}) is already in the past.')
        return redirect('admin_elections')
    if election.start_date < now:
        messages.warning(request, f'Note: "{election.title}" start date is in the past. Voters can still cast ballots until the end date.')
    election.is_active = True
    election.save()
    log_audit(request.user, f'Activated election: {election.title}', request=request)
    messages.success(request, f'"{election.title}" is now active! Voters can cast ballots.')
    return redirect('admin_elections')


@login_required
@user_passes_test(is_admin)
def admin_candidates(request):
    """Admin: Approve or reject candidate registrations.
    Pending candidates appear at top with Approve/Reject buttons."""
    candidates = Candidate.objects.all()
    pending = Candidate.objects.filter(approval_status='pending')

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')
        action = request.POST.get('action')
        candidate = get_object_or_404(Candidate, id=candidate_id)
        if action == 'approve':
            candidate.is_approved = True
            candidate.approval_status = 'approved'
            candidate.user.role = 'candidate'
            candidate.user.save()
            candidate.save()
            log_audit(request.user, f'Approved candidate: {candidate.user.username}', request=request)
            messages.success(request, 'Candidate approved!')
        elif action == 'reject':
            candidate.is_approved = False
            candidate.approval_status = 'rejected'
            candidate.user.role = 'voter'
            candidate.user.save()
            candidate.save()
            log_audit(request.user, f'Rejected candidate: {candidate.user.username}', request=request)
            messages.success(request, f'Candidate {candidate.user.username} rejected (reverted to voter).')
        return redirect('admin_candidates')

    approved = Candidate.objects.filter(approval_status='approved')
    rejected = Candidate.objects.filter(approval_status='rejected')
    return render(request, 'core/admin_candidates.html', {
        'candidates': candidates, 'pending': pending,
        'approved': approved, 'rejected': rejected,
    })


@login_required
@user_passes_test(is_admin)
def admin_audit_logs(request):
    """Admin: View the last 100 audit log entries.
    Every vote, registration, approval, etc. is recorded here."""
    logs = AuditLog.objects.all()[:100]
    return render(request, 'core/admin_audit.html', {'logs': logs})


# ═══════════════════════════════════════════════════════════════
# API VIEWS (Django REST Framework) — return JSON, not HTML
# ═══════════════════════════════════════════════════════════════

# Each ViewSet below provides automatic CRUD endpoints:
# GET    /api/elections/     → list all
# POST   /api/elections/     → create new
# GET    /api/elections/1/   → get detail
# PUT    /api/elections/1/   → update
# DELETE /api/elections/1/   → delete

class UserViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ElectionViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete elections"""
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PositionViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete positions"""
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CandidateViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete candidates.
    Includes computed vote_count in the response."""
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ManifestoViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete manifestos"""
    queryset = Manifesto.objects.all()
    serializer_class = ManifestoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class VoteViewSet(viewsets.ReadOnlyModelViewSet):
    """API: List own votes only. Votes cannot be modified via API."""
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vote.objects.filter(voter=self.request.user)


class ManifestoUpdateViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete manifesto progress updates"""
    queryset = ManifestoUpdate.objects.all()
    serializer_class = ManifestoUpdateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ManifestoRatingViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete manifesto ratings.
    The rater is set automatically to the logged-in user."""
    queryset = ManifestoRating.objects.all()
    serializer_class = ManifestoRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AuditLogViewSet(viewsets.ModelViewSet):
    """API: List audit logs (admin only)"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]


# ─── CUSTOM API ENDPOINTS (not CRUD, but computed data) ─────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_election_results(request, election_id):
    """GET /api/elections/1/results/
    Returns election results with vote counts per candidate,
    sorted by votes descending."""
    election = get_object_or_404(Election, id=election_id)
    results = []
    for position in election.positions.all():
        candidates = Candidate.objects.filter(position=position, is_approved=True)
        data = [{
            'candidate_id': c.id,
            'name': c.user.get_full_name() or c.user.username,
            'votes': Vote.objects.filter(candidate=c, election=election).count(),
        } for c in candidates]
        data.sort(key=lambda x: x['votes'], reverse=True)
        results.append({'position': position.title, 'candidates': data})
    return Response({'election': election.title, 'results': results})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_manifesto_tracking(request, election_id):
    """GET /api/elections/1/tracking/
    Returns full manifesto tracking data for an election:
    each candidate's manifestos with their latest status and all updates."""
    election = get_object_or_404(Election, id=election_id)
    data = []
    for candidate in Candidate.objects.filter(election=election, is_approved=True):
        manifestos = []
        for m in Manifesto.objects.filter(candidate=candidate):
            updates = ManifestoUpdate.objects.filter(manifesto=m)
            latest = updates.first()
            manifestos.append({
                'id': m.id, 'title': m.title, 'categories': [cat.name for cat in m.categories.all()],
                'latest_status': latest.status if latest else 'not_started',
                'updates': ManifestoUpdateSerializer(updates, many=True).data,
            })
        data.append({
            'candidate_id': candidate.id,
            'name': candidate.user.get_full_name() or candidate.user.username,
            'position': candidate.position.title if candidate.position else None,
            'manifestos': manifestos,
        })
    return Response({'election': election.title, 'candidates': data})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_leaderboard(request):
    """GET /api/leaderboard/
    Returns all candidates ranked by average star rating only."""
    candidates = Candidate.objects.filter(is_approved=True)
    data = []
    for c in candidates:
        avg_rating = ManifestoRating.objects.filter(manifesto__candidate=c).aggregate(
            avg=models.Avg('rating')
        )['avg']
        data.append({
            'candidate_id': c.id,
            'name': c.user.get_full_name() or c.user.username,
            'position': c.position.title if c.position else None,
            'election': c.election.title,
            'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        })
    data.sort(key=lambda x: x['avg_rating'], reverse=True)
    for i, d in enumerate(data, 1):
        d['rank'] = i
    return Response({'leaderboard': data})
