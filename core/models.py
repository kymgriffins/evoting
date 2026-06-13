# Django's database modelling tools
from django.db import models
# Built-in user system — we extend it with custom fields
from django.contrib.auth.models import AbstractUser


# ──────────────────────────────────────────────────────────────
# USER — Extends Django's built-in user with role & student_id
# ──────────────────────────────────────────────────────────────
# Django's default User has: username, password, email, first_name, last_name
# We add: role (voter/candidate/admin), is_verified, student_id
class User(AbstractUser):
    ROLE_CHOICES = (
        ('voter', 'Voter'),
        ('candidate', 'Candidate'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='voter')
    is_verified = models.BooleanField(default=False)
    student_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ──────────────────────────────────────────────────────────────
# ELECTION — A voting event (e.g. "CUEA Student Council 2026")
# ──────────────────────────────────────────────────────────────
# Each election has a time window (start_date → end_date)
# is_active controls whether voters can see/cast ballots
class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ──────────────────────────────────────────────────────────────
# POSITION — A role within an election (President, VP, etc.)
# ──────────────────────────────────────────────────────────────
# Each election has multiple positions. Each position has candidates.
# max_votes = how many candidates a voter can choose (usually 1)
class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_votes = models.IntegerField(default=1)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} - {self.election.title}"


# ──────────────────────────────────────────────────────────────
# CANDIDATE — A person running for a position in an election
# ──────────────────────────────────────────────────────────────
# OneToOneField → each User can be a candidate only once
# approval_status → pending / approved / rejected (admin controls this)
# is_approved → kept for backward compatibility, derived from approval_status
# 
# PROPERTIES (calculated, not stored in DB):
#   success_rate  → % of manifestos marked completed
#   avg_rating    → average star rating across all their manifestos
#   total_ratings → number of ratings received
class Candidate(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, related_name='candidates')
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    bio = models.TextField(blank=True)
    photo = models.URLField(blank=True, help_text='URL to candidate photo')
    is_approved = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position__order', 'user__username']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.position}"

    @property
    def success_rate(self):
        total = Manifesto.objects.filter(candidate=self).count()
        if total == 0:
            return 0
        # Count distinct manifestos that have at least one "completed" update
        completed = ManifestoUpdate.objects.filter(
            manifesto__candidate=self, status='completed'
        ).values('manifesto').distinct().count()
        return round((completed / total) * 100, 1)

    @property
    def avg_rating(self):
        from django.db.models import Avg
        result = ManifestoRating.objects.filter(manifesto__candidate=self).aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] else 0

    @property
    def total_ratings(self):
        return ManifestoRating.objects.filter(manifesto__candidate=self).count()


# ──────────────────────────────────────────────────────────────
# CATEGORY — Dynamic category for manifestos
# ──────────────────────────────────────────────────────────────
# Admin can create/edit categories. Each manifesto can have
# one or more categories assigned to it.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────────────────────
# MANIFESTO — A single campaign promise made by a candidate
# ──────────────────────────────────────────────────────────────
# Each candidate can have multiple manifestos across categories
# Categories are now dynamic via the Category model (M2M)
class Manifesto(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='manifestos')
    title = models.CharField(max_length=200)
    description = models.TextField()
    categories = models.ManyToManyField(Category, related_name='manifestos', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ──────────────────────────────────────────────────────────────
# VOTE — A single vote cast by a voter for a candidate
# ──────────────────────────────────────────────────────────────
# unique_together = [voter, position, election] → prevents double voting
# Each vote links voter → candidate → position → election
class Vote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='votes')
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['voter', 'position', 'election']

    def __str__(self):
        return f"{self.voter.username} -> {self.candidate}"


# ──────────────────────────────────────────────────────────────
# MANIFESTO UPDATE — Progress update on a manifesto promise
# ──────────────────────────────────────────────────────────────
# After election, candidates post updates showing progress
# Status: Not Started → In Progress → Completed / Delayed
# evidence_url: link to supporting document/photo
class ManifestoUpdate(models.Model):
    STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    )
    manifesto = models.ForeignKey(Manifesto, on_delete=models.CASCADE, related_name='updates')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    description = models.TextField()
    evidence_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.manifesto.title} - {self.get_status_display()}"


# ──────────────────────────────────────────────────────────────
# MANIFESTO RATING — User rating & comment on a manifesto
# ──────────────────────────────────────────────────────────────
# Voters rate each manifesto 1-5 stars and leave optional comments
# unique_together → one rating per user per manifesto
class ManifestoRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    manifesto = models.ForeignKey(Manifesto, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'manifesto']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.manifesto.title}: {self.rating}/5"


# ──────────────────────────────────────────────────────────────
# AUDIT LOG — Every important action is recorded here
# ──────────────────────────────────────────────────────────────
# Replaces blockchain: we log user, action, details, IP, timestamp
# Everything is auditable, searchable, and can't be deleted
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
