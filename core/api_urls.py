# api_urls.py — Maps API endpoints to API views.
# Uses DRF's DefaultRouter which automatically creates:
#   GET/POST  /api/users/        → list/create
#   GET/PUT/DELETE  /api/users/1/  → detail/update/delete
# Plus custom endpoints at the bottom.

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ── Router generates CRUD endpoints automatically ────────────
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'elections', views.ElectionViewSet)
router.register(r'positions', views.PositionViewSet)
router.register(r'candidates', views.CandidateViewSet)
router.register(r'manifestos', views.ManifestoViewSet)
router.register(r'votes', views.VoteViewSet, basename='vote')
router.register(r'updates', views.ManifestoUpdateViewSet)
router.register(r'ratings', views.ManifestoRatingViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)

# ── Custom endpoints (not CRUD) ──────────────────────────────
urlpatterns = [
    path('', include(router.urls)),
    path('elections/<int:election_id>/results/', views.api_election_results, name='api_election_results'),
    path('elections/<int:election_id>/tracking/', views.api_manifesto_tracking, name='api_manifesto_tracking'),
    path('leaderboard/', views.api_leaderboard, name='api_leaderboard'),
]
