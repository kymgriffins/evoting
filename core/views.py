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

from .models import User, Election, Position, Candidate, Manifesto, Vote, ManifestoUpdate, ManifestoRating, AuditLog
from .forms import (UserRegisterForm, CandidateForm, ManifestoForm,
                    ManifestoUpdateForm, ManifestoRatingForm, ElectionForm, PositionForm)
from .serializers import (UserSerializer, ElectionSerializer, PositionSerializer,
                          CandidateSerializer, ManifestoSerializer, VoteSerializer,
                          ManifestoUpdateSerializer, ManifestoRatingSerializer, AuditLogSerializer)


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
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def results(request, election_id=None):
    """Public election results page — shows vote counts per candidate.
    If election_id is given, shows that election. Otherwise shows all past elections."""
    if election_id:
        elections = Election.objects.filter(id=election_id)
    else:
        elections = Election.objects.filter(end_date__lt=timezone.now())

    results_data = []
    for election in elections:
        positions_data = []
        for position in election.positions.all():
            candidates = Candidate.objects.filter(position=position, is_approved=True)
            candidate_data = []
            for c in candidates:
                vote_count = Vote.objects.filter(candidate=c, election=election).count()
                candidate_data.append({'candidate': c, 'vote_count': vote_count})
            candidate_data.sort(key=lambda x: x['vote_count'], reverse=True)  # Highest votes first
            positions_data.append({'position': position, 'candidates': candidate_data})
        results_data.append({'election': election, 'positions': positions_data})

    return render(request, 'core/results.html', {'results': results_data})


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
                    'latest_status': latest_update.get_status_display() if latest_update else 'Not Started',
                    'updates_count': ManifestoUpdate.objects.filter(manifesto=m).count(),
                    'avg_rating': round(avg_rating, 1) if avg_rating else 0,
                    'rating_count': rating_count,
                })
            candidates_data.append({'candidate': c, 'manifestos': manifestos_data})
        tracking_data.append({'election': election, 'candidates': candidates_data})

    return render(request, 'core/manifesto_tracking.html', {'tracking_data': tracking_data})


def leaderboard(request):
    """Public leaderboard — ranks candidates by success rate.
    Success rate = % of manifesto items that have been completed.
    Sorts by success_rate DESC, then avg_rating DESC.
    Top 3 get medals on the HTML page."""
    candidates = Candidate.objects.filter(is_approved=True).select_related('user', 'position', 'election')
    ranking = []
    for c in candidates:
        total_manif = Manifesto.objects.filter(candidate=c).count()
        if total_manif == 0:
            continue
        completed = ManifestoUpdate.objects.filter(
            manifesto__candidate=c, status='completed'
        ).values('manifesto').distinct().count()
        success_rate = round((completed / total_manif) * 100, 1)
        rating_count = ManifestoRating.objects.filter(manifesto__candidate=c).count()
        avg_rating = ManifestoRating.objects.filter(manifesto__candidate=c).aggregate(
            avg=models.Avg('rating')
        )['avg']
        total_votes = Vote.objects.filter(candidate=c).count()

        ranking.append({
            'candidate': c,
            'total_manifestos': total_manif,
            'completed_manifestos': completed,
            'success_rate': success_rate,
            'avg_rating': round(avg_rating, 1) if avg_rating else 0,
            'rating_count': rating_count,
            'total_votes': total_votes,
        })

    ranking.sort(key=lambda x: (x['success_rate'], x['avg_rating']), reverse=True)
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

        election_stats = []
        for e in all_elections:
            vc = Vote.objects.filter(election=e).count()
            cc = Candidate.objects.filter(election=e, is_approved=True).count()
            mc = Manifesto.objects.filter(candidate__election=e).count()
            election_stats.append({'election': e, 'votes': vc, 'candidates': cc, 'manifestos': mc})

        return render(request, 'core/dashboard.html', {
            'section': 'admin', 'now': timezone.now(),
            'total_voters': total_voters, 'total_candidates': total_candidates_count,
            'total_votes': total_votes, 'pending_candidates': pending_candidates,
            'total_manifestos': total_manifestos, 'total_updates': total_updates,
            'active_elections': active_elections, 'past_elections': past_elections,
            'all_elections': all_elections, 'election_stats': election_stats,
        })

    elif user.role == 'candidate':
        try:
            candidate = user.candidate_profile
        except Candidate.DoesNotExist:
            return redirect('candidate_setup')
        my_manifestos = Manifesto.objects.filter(candidate=candidate)
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
    Admin must approve before they appear on ballot."""
    if request.user.role != 'candidate':
        messages.error(request, 'You must register as a candidate first.')
        return redirect('register')

    if Candidate.objects.filter(user=request.user).exists():
        return redirect('dashboard')

    active_elections = Election.objects.filter(is_active=True)
    positions = Position.objects.filter(election__in=active_elections)
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.user = request.user
            candidate.election_id = request.POST.get('election')
            candidate.save()
            log_audit(request.user, 'Candidate profile created', request=request)
            messages.success(request, 'Candidate profile created! Awaiting admin approval.')
            return redirect('dashboard')
    else:
        form = CandidateForm()

    return render(request, 'core/candidate_setup.html', {
        'form': form, 'elections': active_elections, 'positions': positions,
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

    manifestos = Manifesto.objects.filter(candidate=candidate)
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
            log_audit(request.user, f'Manifesto created: {manifesto.title}', request=request)
            messages.success(request, 'Manifesto item added!')
            return redirect('manage_manifestos')
    else:
        form = ManifestoForm()
    return render(request, 'core/manifesto_form.html', {'form': form, 'editing': False})


@login_required
def manifesto_edit(request, pk):
    """Edit an existing manifesto"""
    manifesto = get_object_or_404(Manifesto, pk=pk, candidate__user=request.user)
    if request.method == 'POST':
        form = ManifestoForm(request.POST, instance=manifesto)
        if form.is_valid():
            form.save()
            log_audit(request.user, f'Manifesto updated: {manifesto.title}', request=request)
            messages.success(request, 'Manifesto updated!')
            return redirect('manage_manifestos')
    else:
        form = ManifestoForm(instance=manifesto)
    return render(request, 'core/manifesto_form.html', {'form': form, 'editing': True})


@login_required
def manifesto_delete(request, pk):
    """Delete a manifesto"""
    manifesto = get_object_or_404(Manifesto, pk=pk, candidate__user=request.user)
    log_audit(request.user, f'Manifesto deleted: {manifesto.title}', request=request)
    manifesto.delete()
    messages.success(request, 'Manifesto deleted.')
    return redirect('manage_manifestos')


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
        pos.candidates = Candidate.objects.filter(position=pos, is_approved=True)
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
            form.save()
            log_audit(request.user, 'Election created', request=request)
            messages.success(request, 'Election created!')
            return redirect('admin_elections')
    else:
        form = ElectionForm()

    elections = Election.objects.all()
    return render(request, 'core/admin_elections.html', {
        'form': form, 'elections': elections,
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
    else:
        form = ElectionForm(instance=election)
    return render(request, 'core/admin_elections.html', {
        'form': form, 'editing': True, 'elections': Election.objects.all(),
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
    else:
        form = PositionForm()

    positions = Position.objects.filter(election=election)
    return render(request, 'core/admin_positions.html', {
        'form': form, 'election': election, 'positions': positions,
    })


@login_required
@user_passes_test(is_admin)
def admin_candidates(request):
    """Admin: Approve or reject candidate registrations.
    Pending candidates appear at top with Approve/Reject buttons."""
    candidates = Candidate.objects.all()
    pending = Candidate.objects.filter(is_approved=False)

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')
        action = request.POST.get('action')
        candidate = get_object_or_404(Candidate, id=candidate_id)
        if action == 'approve':
            candidate.is_approved = True
            candidate.user.role = 'candidate'
            candidate.user.save()
            candidate.save()
            log_audit(request.user, f'Approved candidate: {candidate.user.username}', request=request)
            messages.success(request, 'Candidate approved!')
        elif action == 'reject':
            log_audit(request.user, f'Rejected candidate: {candidate.user.username}', request=request)
            candidate.delete()
            messages.success(request, 'Candidate rejected.')
        return redirect('admin_candidates')

    return render(request, 'core/admin_candidates.html', {
        'candidates': candidates, 'pending': pending,
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


class VoteViewSet(viewsets.ModelViewSet):
    """API: List/create votes. The voter is set automatically
    to the currently logged-in user."""
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(voter=self.request.user)


class ManifestoUpdateViewSet(viewsets.ModelViewSet):
    """API: List/create/update/delete manifesto progress updates"""
    queryset = ManifestoUpdate.objects.all()
    serializer_class = ManifestoUpdateSerializer
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
                'id': m.id, 'title': m.title, 'category': m.category,
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
    Returns all candidates ranked by success rate (completed manifestos / total)
    and average star rating. Used by external apps/widgets."""
    candidates = Candidate.objects.filter(is_approved=True)
    data = []
    for c in candidates:
        total = Manifesto.objects.filter(candidate=c).count()
        completed = ManifestoUpdate.objects.filter(
            manifesto__candidate=c, status='completed'
        ).values('manifesto').distinct().count()
        avg_rating = ManifestoRating.objects.filter(manifesto__candidate=c).aggregate(
            avg=models.Avg('rating')
        )['avg']
        data.append({
            'candidate_id': c.id,
            'name': c.user.get_full_name() or c.user.username,
            'position': c.position.title if c.position else None,
            'election': c.election.title,
            'total_manifestos': total,
            'completed_manifestos': completed,
            'success_rate': round((completed / total) * 100, 1) if total else 0,
            'avg_rating': round(avg_rating, 1) if avg_rating else 0,
            'total_votes': Vote.objects.filter(candidate=c).count(),
        })
    data.sort(key=lambda x: (x['success_rate'], x['avg_rating']), reverse=True)
    for i, d in enumerate(data, 1):
        d['rank'] = i
    return Response({'leaderboard': data})
