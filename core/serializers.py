# serializers.py — Converts database models to JSON (for the REST API).
# Each serializer defines which fields are included in API responses.
# DRF (Django REST Framework) handles JSON serialization automatically.

from rest_framework import serializers
from .models import User, Election, Position, Candidate, Manifesto, Vote, ManifestoUpdate, ManifestoRating, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """API representation of a User.
    Excludes password for security — only id, username, email, role, etc."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_verified', 'student_id']
        read_only_fields = ['id']  # id is auto-generated, can't be set via API


class ElectionSerializer(serializers.ModelSerializer):
    """API representation of an Election — includes all fields"""
    class Meta:
        model = Election
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):
    """API representation of a Position"""
    class Meta:
        model = Position
        fields = '__all__'


class CandidateSerializer(serializers.ModelSerializer):
    """API representation of a Candidate.
    Includes nested user details and live vote count."""
    user_details = UserSerializer(source='user', read_only=True)
    vote_count = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = '__all__'
        read_only_fields = ['vote_count']

    def get_vote_count(self, obj):
        """Calculates how many votes this candidate received"""
        return obj.votes.count()


class ManifestoSerializer(serializers.ModelSerializer):
    """API representation of a Manifesto"""
    class Meta:
        model = Manifesto
        fields = '__all__'


class VoteSerializer(serializers.ModelSerializer):
    """API representation of a Vote. Only creation allowed — no editing."""
    class Meta:
        model = Vote
        fields = '__all__'
        read_only_fields = ['voter', 'timestamp']


class ManifestoUpdateSerializer(serializers.ModelSerializer):
    """API representation of a Manifesto progress update"""
    class Meta:
        model = ManifestoUpdate
        fields = '__all__'


class ManifestoRatingSerializer(serializers.ModelSerializer):
    """API representation of a Manifesto rating.
    User and created_at are set automatically, not via API."""
    class Meta:
        model = ManifestoRating
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """API representation of an Audit Log entry"""
    class Meta:
        model = AuditLog
        fields = '__all__'
