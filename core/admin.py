# admin.py — Configures Django's built-in admin panel at /admin/
# Controls how models appear when you login as a superuser.

from django.contrib import admin
from .models import User, Election, Position, Candidate, Manifesto, Vote, ManifestoUpdate, ManifestoRating, AuditLog


class UserAdmin(admin.ModelAdmin):
    """Customize the User list view in admin panel.
    Shows username, email, role, verification status at a glance.
    Admins can filter by role and verification status."""
    list_display = ['username', 'email', 'role', 'is_verified', 'is_staff']
    list_filter = ['role', 'is_verified']


class CandidateAdmin(admin.ModelAdmin):
    """Customize the Candidate list view.
    Shows user, position, election, and approval status.
    Admins can filter by approval status and election."""
    list_display = ['user', 'position', 'election', 'is_approved']
    list_filter = ['is_approved', 'election']


class VoteAdmin(admin.ModelAdmin):
    """Vote viewing only — no editing or deleting to preserve integrity."""
    list_display = ['voter', 'candidate', 'position', 'election', 'timestamp']
    list_filter = ['election']

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


# Register all models with the admin panel
admin.site.register(User, UserAdmin)
admin.site.register(Election)
admin.site.register(Position)
admin.site.register(Candidate, CandidateAdmin)
admin.site.register(Manifesto)
admin.site.register(Vote, VoteAdmin)
admin.site.register(ManifestoUpdate)
admin.site.register(ManifestoRating)
admin.site.register(AuditLog)
