# urls.py — MASTER URL MAP.
# Every web address the app responds to is listed here.
# Django matches the URL → calls the corresponding view function.

from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views  # Django's built-in login/logout

from core import views

urlpatterns = [
    # ── Public Pages (no login required) ────────────────────
    path('', views.home, name='home'),                           # Landing page
    path('register/', views.register, name='register'),           # User registration
    path('login/', auth_views.LoginView.as_view(                  # Login (built-in Django view)
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Logout
    path('results/', views.results, name='results'),              # All past election results
    path('results/<int:election_id>/', views.results,             # Specific election results
         name='results_detail'),
    path('tracking/', views.manifesto_tracking,                   # Manifesto tracking dashboard
         name='manifesto_tracking'),
    path('tracking/<int:election_id>/', views.manifesto_tracking, # Tracking for specific election
         name='manifesto_tracking_detail'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),  # Candidate performance rankings

    # ── Authenticated Pages (must be logged in) ─────────────
    path('dashboard/', views.dashboard, name='dashboard'),        # Role-based dashboard

    # Candidate setup
    path('candidate/setup/', views.candidate_setup,               # First-time candidate profile
         name='candidate_setup'),

    # Manifesto management (candidates only)
    path('candidate/manifestos/', views.manage_manifestos,        # List my manifestos
         name='manage_manifestos'),
    path('candidate/manifestos/create/', views.manifesto_create,  # Create new manifesto
         name='manifesto_create'),
    path('candidate/manifestos/<int:pk>/edit/', views.manifesto_edit, # Edit manifesto
         name='manifesto_edit'),
    path('candidate/manifestos/<int:pk>/delete/', views.manifesto_delete, # Delete manifesto
         name='manifesto_delete'),
    path('candidate/manifestos/<int:manifesto_pk>/updates/',      # Manifesto detail + updates
         views.manifesto_updates, name='manifesto_updates'),

    # Voting
    path('vote/<int:election_id>/', views.vote_page, name='vote'), # Cast ballot

    # Rating
    path('manifesto/<int:manifesto_pk>/rate/',                     # Rate a manifesto
         views.rate_manifesto, name='rate_manifesto'),

    # ── Admin Pages ─────────────────────────────────────────
    path('admin/elections/', views.admin_elections,                # Manage elections
         name='admin_elections'),
    path('admin/elections/<int:pk>/edit/', views.admin_election_edit, # Edit election
         name='admin_election_edit'),
    path('admin/elections/<int:election_id>/positions/',           # Manage positions
         views.admin_positions, name='admin_positions'),
    path('admin/candidates/', views.admin_candidates,              # Approve/reject candidates
         name='admin_candidates'),
    path('admin/logs/', views.admin_audit_logs,                    # View audit logs
         name='admin_audit_logs'),

    # ── Django Admin Panel ──────────────────────────────────
    # Built-in admin interface. Login as superuser to access.
    path('admin/', admin.site.urls),

    # ── API Endpoints ───────────────────────────────────────
    path('api/', include('core.api_urls')),                        # All API routes
]
