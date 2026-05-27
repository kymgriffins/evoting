# forms.py — Defines all HTML forms used in the app.
# Each form maps to a model and controls what fields users can fill in.
# Django handles validation, error messages, and HTML rendering automatically.

from django import forms
from django.contrib.auth.forms import UserCreationForm  # Built-in Django registration form
from .models import User, Candidate, Manifesto, ManifestoUpdate, ManifestoRating, Election, Position


class UserRegisterForm(UserCreationForm):
    """Registration form — extends Django's built-in form with role & student_id.
    Django's UserCreationForm already has: username, password1, password2
    We add: email, student_id, role (voter or candidate)"""
    email = forms.EmailField(required=True)
    student_id = forms.CharField(max_length=50, required=False)
    role = forms.ChoiceField(choices=[('voter', 'Voter'), ('candidate', 'Candidate')])

    class Meta:
        model = User
        fields = ['username', 'email', 'student_id', 'role', 'password1', 'password2']


class CandidateForm(forms.ModelForm):
    """Form for candidates to set up their profile.
    Admin approval is handled separately."""
    class Meta:
        model = Candidate
        fields = ['position', 'bio', 'photo']


class ManifestoForm(forms.ModelForm):
    """Form to create/edit a manifesto (campaign promise).
    Title, description, and category are required."""
    class Meta:
        model = Manifesto
        fields = ['title', 'description', 'category']


class ManifestoUpdateForm(forms.ModelForm):
    """Form for candidates to post progress updates on their promises.
    Status: Not Started / In Progress / Completed / Delayed"""
    class Meta:
        model = ManifestoUpdate
        fields = ['status', 'description', 'evidence_url']


class ManifestoRatingForm(forms.ModelForm):
    """Form for voters to rate manifestos 1-5 stars.
    Rating is a radio button selection. Comment is optional."""
    class Meta:
        model = ManifestoRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]
            ),
        }


class ElectionForm(forms.ModelForm):
    """Admin form to create/edit elections.
    Uses datetime-local input for start/end date picking."""
    class Meta:
        model = Election
        fields = ['title', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class PositionForm(forms.ModelForm):
    """Admin form to add positions to an election (President, VP, etc.)"""
    class Meta:
        model = Position
        fields = ['title', 'description', 'order']
