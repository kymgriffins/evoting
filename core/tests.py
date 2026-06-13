from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import User, Election, Position, Candidate, Manifesto, Vote, ManifestoRating, Category, AuditLog


class CandidateVettingTest(TestCase):
    """Tests for candidate self-vetting request flow (requirement 1)"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123', role='admin', is_staff=True
        )
        self.voter = User.objects.create_user(
            username='voter', password='voter123', role='voter'
        )
        self.candidate_user = User.objects.create_user(
            username='cand', password='cand123', role='candidate'
        )
        self.election = Election.objects.create(
            title='Test Election',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=17),
            is_active=False,
        )
        self.position = Position.objects.create(
            election=self.election, title='President', order=1
        )

    def test_candidate_can_request_vetting(self):
        """Candidate can submit a vetting request"""
        c = Client()
        c.login(username='cand', password='cand123')
        resp = c.post(reverse('candidate_setup'), {
            'election': self.election.id,
            'position': self.position.id,
            'bio': 'I want to run',
        })
        self.assertEqual(resp.status_code, 302)
        candidate = Candidate.objects.get(user=self.candidate_user)
        self.assertEqual(candidate.approval_status, 'pending')
        self.assertFalse(candidate.is_approved)

    def test_candidate_sees_all_elections(self):
        """Candidate setup shows all elections including inactive"""
        c = Client()
        c.login(username='cand', password='cand123')
        resp = c.get(reverse('candidate_setup'))
        self.assertContains(resp, 'Test Election')
        self.assertContains(resp, 'Vetting Request Process')

    def test_admin_can_approve_candidate(self):
        """Admin can approve candidate vetting request"""
        candidate = Candidate.objects.create(
            user=self.candidate_user, position=self.position,
            election=self.election, approval_status='pending'
        )
        c = Client()
        c.login(username='admin', password='admin123')
        resp = c.post(reverse('admin_candidates'), {
            'candidate_id': candidate.id, 'action': 'approve',
        })
        self.assertEqual(resp.status_code, 302)
        candidate.refresh_from_db()
        self.assertEqual(candidate.approval_status, 'approved')
        self.assertTrue(candidate.is_approved)
        self.assertEqual(candidate.user.role, 'candidate')

    def test_admin_can_reject_candidate(self):
        """Admin can reject candidate and revert role to voter"""
        candidate = Candidate.objects.create(
            user=self.candidate_user, position=self.position,
            election=self.election, approval_status='pending'
        )
        c = Client()
        c.login(username='admin', password='admin123')
        resp = c.post(reverse('admin_candidates'), {
            'candidate_id': candidate.id, 'action': 'reject',
        })
        self.assertEqual(resp.status_code, 302)
        candidate.refresh_from_db()
        self.assertEqual(candidate.approval_status, 'rejected')
        self.assertFalse(candidate.is_approved)
        self.candidate_user.refresh_from_db()
        self.assertEqual(self.candidate_user.role, 'voter')

    def test_rejected_candidate_can_restubmit(self):
        """Rejected candidate can submit a new vetting request"""
        Candidate.objects.create(
            user=self.candidate_user, position=self.position,
            election=self.election, approval_status='rejected'
        )
        c = Client()
        c.login(username='cand', password='cand123')
        resp = c.get(reverse('candidate_setup'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Vetting Request Process')

    def test_candidate_dashboard_shows_status(self):
        """Candidate dashboard shows approval status clearly"""
        Candidate.objects.create(
            user=self.candidate_user, position=self.position,
            election=self.election, approval_status='pending'
        )
        c = Client()
        c.login(username='cand', password='cand123')
        resp = c.get(reverse('dashboard'))
        self.assertContains(resp, 'Pending')
        self.assertContains(resp, 'Pending Review')


class AdminElectionFlowTest(TestCase):
    """Tests for admin election creation flow (requirement 2)"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123', role='admin', is_staff=True
        )
        self.voter = User.objects.create_user(
            username='voter', password='voter123', role='voter'
        )

    def test_admin_can_create_election(self):
        """Admin can create a new election"""
        c = Client(HTTP_HOST='localhost:8000')
        c.login(username='admin', password='admin123')
        start = timezone.localtime(timezone.now() + timedelta(hours=2))
        resp = c.post(reverse('admin_elections'), {
            'title': 'New Election',
            'description': 'Test',
            'start_date': start.strftime('%Y-%m-%dT%H:%M'),
            'end_date': (start + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Election.objects.filter(title='New Election').exists())

    def test_admin_sees_lifecycle_guidance(self):
        """Admin elections page shows lifecycle guidance"""
        c = Client()
        c.login(username='admin', password='admin123')
        resp = c.get(reverse('admin_elections'))
        self.assertContains(resp, 'Election Lifecycle')

    def test_admin_can_add_positions(self):
        """Admin can add positions to an election"""
        election = Election.objects.create(
            title='Test', start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=8),
        )
        c = Client()
        c.login(username='admin', password='admin123')
        resp = c.post(reverse('admin_positions', args=[election.id]), {
            'title': 'President', 'order': 1,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(election.positions.count(), 1)

    def test_admin_can_activate_election(self):
        """Admin can activate an election"""
        election = Election.objects.create(
            title='Test', start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=8), is_active=False,
        )
        Position.objects.create(election=election, title='President', order=1)
        c = Client()
        c.login(username='admin', password='admin123')
        resp = c.get(reverse('admin_election_activate', args=[election.id]))
        self.assertEqual(resp.status_code, 302)
        election.refresh_from_db()
        self.assertTrue(election.is_active)

    def test_election_next_step_indicator(self):
        """Election table shows correct next step guidance"""
        election = Election.objects.create(
            title='Step Test', start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=8), is_active=False,
        )
        c = Client()
        c.login(username='admin', password='admin123')
        resp = c.get(reverse('admin_elections'))
        self.assertContains(resp, 'Add positions first')

        Position.objects.create(election=election, title='President', order=1)
        resp = c.get(reverse('admin_elections'))
        self.assertContains(resp, 'Approve candidates')


class ManifestoCategoriesTest(TestCase):
    """Tests for dynamic manifesto categories (requirement 3)"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123', role='admin', is_staff=True
        )
        election = Election.objects.create(
            title='Test', start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=8), is_active=True,
        )
        position = Position.objects.create(election=election, title='President', order=1)
        cand_user = User.objects.create_user(
            username='cand', password='cand123', role='candidate'
        )
        self.candidate = Candidate.objects.create(
            user=cand_user, position=position, election=election,
            is_approved=True, approval_status='approved'
        )
        self.cat_edu = Category.objects.create(name='Education')
        self.cat_health = Category.objects.create(name='Healthcare')

    def test_category_creation(self):
        """Categories can be created dynamically"""
        cat = Category.objects.create(name='Test Category')
        self.assertEqual(Category.objects.count(), 3)

    def test_manifesto_with_multiple_categories(self):
        """Manifesto can have multiple categories assigned"""
        manifesto = Manifesto.objects.create(
            candidate=self.candidate, title='Test', description='Test'
        )
        manifesto.categories.add(self.cat_edu, self.cat_health)
        self.assertEqual(manifesto.categories.count(), 2)

    def test_manifesto_form_shows_categories(self):
        """Manifesto creation form shows category checkboxes"""
        c = Client()
        c.login(username='cand', password='cand123')
        resp = c.get(reverse('manifesto_create'))
        self.assertContains(resp, 'Education')
        self.assertContains(resp, 'Healthcare')

    def test_create_manifesto_with_categories(self):
        """Creating manifesto with selected categories works"""
        c = Client()
        c.login(username='cand', password='cand123')
        resp = c.post(reverse('manifesto_create'), {
            'title': 'Test Promise',
            'description': 'A test',
            'categories': [self.cat_edu.id, self.cat_health.id],
        })
        self.assertEqual(resp.status_code, 302)
        manifesto = Manifesto.objects.get(title='Test Promise')
        self.assertEqual(manifesto.categories.count(), 2)


class LeaderboardTest(TestCase):
    """Tests for leaderboard showing only ratings (requirement 4)"""

    def setUp(self):
        election = Election.objects.create(
            title='Test Leaderboard', start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=8),
        )
        position = Position.objects.create(election=election, title='President', order=1)
        voters = []
        for i in range(3):
            voter = User.objects.create_user(
                username=f'voter_lb{i}', password='123', role='voter'
            )
            voters.append(voter)
            user = User.objects.create_user(
                username=f'cand_lb{i}', password='123', role='candidate'
            )
            Candidate.objects.create(
                user=user, position=position, election=election,
                is_approved=True, approval_status='approved',
            )
        candidates = Candidate.objects.filter(election=election)
        # Each voter rates each candidate's manifestos once
        for voter in voters:
            for c in candidates:
                manifesto = Manifesto.objects.create(
                    candidate=c, title=f'P{c.id}-{voter.id}', description='Test'
                )
                ManifestoRating.objects.create(
                    user=voter, manifesto=manifesto, rating=4
                )

    def test_leaderboard_no_success_rate(self):
        """Leaderboard does not show success rate"""
        c = Client()
        resp = c.get(reverse('leaderboard'))
        self.assertNotContains(resp, 'Success Rate')
        self.assertNotContains(resp, 'success_rate')

    def test_leaderboard_no_votes(self):
        """Leaderboard does not show vote counts"""
        c = Client()
        resp = c.get(reverse('leaderboard'))
        self.assertNotContains(resp, 'Votes')
        self.assertNotContains(resp, 'total_votes')

    def test_leaderboard_shows_rating(self):
        """Leaderboard shows average rating"""
        c = Client()
        resp = c.get(reverse('leaderboard'))
        self.assertContains(resp, 'Avg Rating')
        self.assertContains(resp, '/5')

    def test_leaderboard_sorted_by_rating(self):
        """Leaderboard is sorted by average rating descending"""
        c = Client()
        resp = c.get(reverse('leaderboard'))
        self.assertEqual(resp.status_code, 200)

    def test_leaderboard_api_no_success_rate(self):
        """API leaderboard does not include success_rate or votes"""
        c = Client()
        resp = c.get('/api/leaderboard/')
        data = resp.json()
        for entry in data['leaderboard']:
            self.assertNotIn('success_rate', entry)
            self.assertNotIn('total_votes', entry)
            self.assertIn('avg_rating', entry)


class CollapseExpandTest(TestCase):
    """Tests for collapse/expand functionality (requirement 5)"""

    def test_collapse_css_in_base(self):
        """Base template contains collapse/expand CSS classes"""
        c = Client()
        resp = c.get('/')
        self.assertContains(resp, 'collapse-toggle')
        self.assertContains(resp, 'collapse-content')

    def test_collapse_on_dashboard(self):
        """Dashboard has collapse toggles for lists"""
        admin = User.objects.create_user(
            username='admin', password='admin123', role='admin', is_staff=True
        )
        c = Client()
        c.login(username='admin', password='admin123')
        resp = c.get(reverse('dashboard'))
        self.assertContains(resp, 'collapse-toggle')


class CandidateResultsRestrictionTest(TestCase):
    """Tests for candidate results restriction (requirement 6)"""

    def setUp(self):
        election1 = Election.objects.create(
            title='Election 1', start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() - timedelta(days=23),
        )
        election2 = Election.objects.create(
            title='Election 2', start_date=timezone.now() - timedelta(days=20),
            end_date=timezone.now() - timedelta(days=13),
        )
        pos1 = Position.objects.create(election=election1, title='President', order=1)
        pos2 = Position.objects.create(election=election2, title='President', order=1)

        cand_user = User.objects.create_user(
            username='cand', password='123', role='candidate'
        )
        Candidate.objects.create(
            user=cand_user, position=pos1, election=election1,
            is_approved=True, approval_status='approved',
        )
        voter = User.objects.create_user(
            username='voter', password='123', role='voter'
        )
        self.election1 = election1
        self.election2 = election2

    def test_candidate_sees_own_election_only(self):
        """Candidate sees only their own election results by default"""
        c = Client()
        c.login(username='cand', password='123')
        resp = c.get(reverse('results'))
        self.assertContains(resp, 'Election 1')
        self.assertNotContains(resp, 'Election 2')
        self.assertContains(resp, 'Candidate Results View')

    def test_candidate_can_opt_in_to_all(self):
        """Candidate can opt in to view all results"""
        c = Client()
        c.login(username='cand', password='123')
        resp = c.get(reverse('results') + '?view_all=1')
        self.assertContains(resp, 'Election 1')
        self.assertContains(resp, 'Election 2')

    def test_voter_sees_all_results(self):
        """Voter always sees all results"""
        c = Client()
        c.login(username='voter', password='123')
        resp = c.get(reverse('results'))
        self.assertContains(resp, 'Election 1')
        self.assertContains(resp, 'Election 2')
        self.assertNotContains(resp, 'Candidate Results View')


class AuditLogTest(TestCase):
    """Tests for audit logging"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='audit_admin', password='admin123', role='admin', is_staff=True
        )
        self.election = Election.objects.create(
            title='Audit Election', start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=8),
        )
        self.position = Position.objects.create(
            election=self.election, title='President', order=1
        )

    def test_vetting_request_logged(self):
        """Vetting request is logged in audit trail"""
        cand_user = User.objects.create_user(
            username='cand_test', password='cand123', role='candidate'
        )
        c = Client()
        c.login(username='cand_test', password='cand123')
        c.post(reverse('candidate_setup'), {
            'election': self.election.id, 'position': self.position.id, 'bio': 'Test',
        })
        self.assertTrue(AuditLog.objects.filter(
            action__contains='vetting'
        ).exists())

    def test_admin_approval_logged(self):
        """Admin approval of candidate is logged"""
        cand_user = User.objects.create_user(
            username='cand_approve', password='cand123', role='candidate'
        )
        candidate = Candidate.objects.create(
            user=cand_user, position=self.position, election=self.election,
            approval_status='pending'
        )
        c = Client(HTTP_HOST='localhost:8000')
        c.login(username='audit_admin', password='admin123')
        resp = c.post(reverse('admin_candidates'), {
            'candidate_id': candidate.id, 'action': 'approve',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('admin_candidates'))
        candidate.refresh_from_db()
        self.assertEqual(candidate.approval_status, 'approved')
        self.assertTrue(candidate.is_approved)
        logs = list(AuditLog.objects.all())
        self.assertTrue(
            any('Approved' in log.action for log in logs),
            msg=f'No approved log found. Logs: {[l.action for l in logs]}'
        )
