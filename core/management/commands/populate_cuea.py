"""
Massive CUEA data population:
- 600 voters, 5 admins, 10 candidates
- 50 manifestos, 70% completed, user ratings on each
- Leaderboard-ready data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from datetime import timedelta
import random, math

from core.models import User, Election, Position, Candidate, Manifesto, Vote, ManifestoUpdate, ManifestoRating, AuditLog

CUEA_SCHOOLS = [
    'School of Science and Technology',
    'School of Education',
    'School of Health Sciences',
    'School of Business and Economics',
    'School of Law',
    'School of Engineering',
]

SCHOOL_ABBR = {s: ''.join(w[0] for w in s.replace('School of ', '').split()) for s in CUEA_SCHOOLS}

MANIFESTO_TEMPLATES = {
    'education': [
        ('Digital Library Access', 'Expand online journal subscriptions and e-book access for all students across every school.'),
        ('Scholarship Transparency Portal', 'Create a public dashboard showing all available scholarships, criteria, and award decisions.'),
        ('Peer Mentorship Network', 'Establish a cross-school mentorship program pairing senior and junior students by discipline.'),
        ('Exam Resource Bank', 'Build a centralized repository of past exam papers, marking schemes, and revision materials.'),
        ('Academic Counseling Center', 'Set up a dedicated center for academic advising, course selection help, and study skill workshops.'),
        ('Research Grant for Undergraduates', 'Introduce small research grants for undergraduate students undertaking final-year projects.'),
        ('Lecture Capture System', 'Install recording equipment in all lecture halls so students can review lectures on-demand.'),
        ('Faculty-Student Forums', 'Organize quarterly town halls where students can raise academic concerns directly with faculty.'),
    ],
    'healthcare': [
        ('24-Hour Clinic Service', 'Extend campus clinic hours to 24/7 with full nursing staff and basic emergency care.'),
        ('Mental Health Hotline', 'Launch a confidential 24-hour mental health support hotline staffed by professional counselors.'),
        ('Free Annual Check-ups', 'Negotiate free annual medical check-ups for all students including dental and eye tests.'),
        ('Health Insurance Scheme', 'Secure affordable comprehensive health insurance coverage for all registered students.'),
        ('Wellness Workshops', 'Run monthly workshops on stress management, nutrition, fitness, and mental well-being.'),
        ('Pharmacy on Campus', 'Establish a fully stocked campus pharmacy with subsidized medication for common ailments.'),
    ],
    'infrastructure': [
        ('Campus-Wide Wi-Fi', 'Deploy high-speed Wi-Fi in every building including hostels, lecture halls, and outdoor common areas.'),
        ('Hostel Modernization', 'Renovate all hostels with new beds, desks, shelving, improved lighting, and better bathrooms.'),
        ('Smart Classrooms', 'Upgrade classrooms with projectors, smart boards, proper acoustics, and comfortable seating.'),
        ('Solar Power Backup', 'Install solar panels and battery backup systems to eliminate power outages during exams.'),
        ('Campus CCTV Network', 'Install comprehensive CCTV coverage across campus parking lots, walkways, and building entrances.'),
        ('Accessible Infrastructure', 'Add ramps, elevators, and accessible washrooms for students with physical disabilities.'),
    ],
    'student_welfare': [
        ('Subsidized Bus Service', 'Launch affordable shuttle buses connecting all campuses and major student residential areas.'),
        ('Food Court Upgrade', 'Improve cafeteria food quality, introduce meal plans, and ensure affordable pricing for all.'),
        ('Student Startup Fund', 'Create a KES 1M seed fund to support student-led business ideas and social enterprises.'),
        ('Career Placement Office', 'Establish a full-time career office offering internships, job placement, and resume workshops.'),
        ('Night Library', 'Keep the main library open 24 hours during exam periods with充足的 lighting and security.'),
        ('Gender-Neutral Facilities', 'Designate gender-neutral washrooms and create a more inclusive campus environment.'),
        ('Students Affairs Mobile App', 'Build a mobile app for accessing grades, registration, events, and campus news.'),
    ],
    'other': [
        ('Cultural Festival', 'Organize an annual inter-school cultural festival showcasing music, dance, art, and cuisine.'),
        ('Environmental Green Corps', 'Form a student-led environmental team for tree planting, recycling drives, and clean-up campaigns.'),
        ('Tech Incubation Hub', 'Create a co-working space with 3D printers, coding bootcamps, and hackathon events.'),
        ('Debate and Public Speaking', 'Revive the university debate society with weekly sessions and inter-university tournaments.'),
        ('Sports League Expansion', 'Expand intramural sports leagues to include more sports and women\'s teams.'),
        ('Community Outreach Program', 'Organize regular outreach to local communities in areas of health, education, and sanitation.'),
    ],
}

ADMINS_DATA = [
    ('admin', 'admin123', 'System', 'Administrator', 'ADM-001'),
    ('admin02', 'admin123', 'Jane', 'Mwikali', 'ADM-002'),
    ('admin03', 'admin123', 'Peter', 'Kamau', 'ADM-003'),
    ('admin04', 'admin123', 'Grace', 'Ndung\'u', 'ADM-004'),
    ('admin05', 'admin123', 'Samuel', 'Ochieng', 'ADM-005'),
]

CANDIDATES_DATA = [
    ('cand001', 'cand123', 'James', 'Mwangi', 'School of Engineering', 'Engineering student committed to modernizing campus infrastructure and championing innovation.'),
    ('cand002', 'cand123', 'Faith', 'Chebet', 'School of Education', 'Education major passionate about academic excellence, mentorship, and student welfare.'),
    ('cand003', 'cand123', 'Kevin', 'Odhiambo', 'School of Health Sciences', 'Health science student advocating for better campus health services and wellness programs.'),
    ('cand004', 'cand123', 'Esther', 'Nyambura', 'School of Business and Economics', 'Business student focused on financial transparency and student entrepreneurship.'),
    ('cand005', 'cand123', 'Daniel', 'Kiprop', 'School of Law', 'Law student committed to upholding student rights and improving governance structures.'),
    ('cand006', 'cand123', 'Sarah', 'Wanjiku', 'School of Science and Technology', 'IT student aiming to digitize council operations and enhance tech access for all students.'),
    ('cand007', 'cand123', 'Michael', 'Ndegwa', 'School of Engineering', 'Civil engineering student with a vision for sustainable campus development.'),
    ('cand008', 'cand123', 'Lucy', 'Akinyi', 'School of Education', 'Education student dedicated to inclusive learning and student-teacher engagement.'),
    ('cand009', 'cand123', 'Brian', 'Omondi', 'School of Business and Economics', 'Economics student focused on student enterprise and financial literacy programs.'),
    ('cand010', 'cand123', 'Grace', 'Mwende', 'School of Law', 'Law student passionate about social justice, legal aid, and campus safety.'),
]


class Command(BaseCommand):
    help = 'Populate CUEA with 600 voters, 5 admins, 10 candidates, 50 manifestos + ratings'

    def handle(self, *args, **options):
        self.stdout.write('Wiping existing data...')
        ManifestoRating.objects.all().delete()
        ManifestoUpdate.objects.all().delete()
        Manifesto.objects.all().delete()
        Vote.objects.all().delete()
        Candidate.objects.all().delete()
        Position.objects.all().delete()
        Election.objects.all().delete()
        AuditLog.objects.all().delete()
        User.objects.all().delete()

        now = timezone.now()

        # ── Pre-compute Hashed Passwords ───────────────────────────
        self.stdout.write('Pre-computing password hashes...')
        hashed_admin_pwd = make_password('admin123')
        hashed_voter_pwd = make_password('voter123')
        hashed_cand_pwd = make_password('cand123')

        # ── 5 Admins ──────────────────────────────────────────────
        self.stdout.write('Creating 5 admins...')
        admin_users = []
        for uname, pwd, first, last, sid in ADMINS_DATA:
            admin_users.append(User(
                username=uname, password=hashed_admin_pwd, email=f'{uname}@cuea.edu',
                role='admin', is_staff=True, is_superuser=(uname == 'admin'),
                is_verified=True, student_id=sid,
                first_name=first, last_name=last,
            ))
        User.objects.bulk_create(admin_users)

        # ── 600 Voters ─────────────────────────────────────────────
        self.stdout.write('Creating 600 voters...')
        voter_batch = []
        all_schools = CUEA_SCHOOLS * 100
        for i in range(1, 601):
            school = all_schools[(i - 1) % len(CUEA_SCHOOLS)]
            abbr = SCHOOL_ABBR[school]
            voter_batch.append(User(
                username=f'v{i:04d}',
                email=f'v{i:04d}@cuea.edu',
                password=hashed_voter_pwd,
                role='voter', is_verified=True,
                student_id=f'{abbr}-2024/{i:04d}',
                first_name=f'Student{i}',
                last_name=school.split()[-1],
            ))
        User.objects.bulk_create(voter_batch, batch_size=100)
        self.stdout.write(f'  Voters: {User.objects.filter(role="voter").count()}')

        # ── 3 Elections ─────────────────────────────────────────────
        self.stdout.write('Creating elections...')
        e2024 = Election.objects.create(
            title='CUEA Student Council Elections 2024',
            description='The 2024 annual student council elections for CUEA.',
            start_date=now - timedelta(days=400),
            end_date=now - timedelta(days=393),
            is_active=False,
        )
        e2025 = Election.objects.create(
            title='CUEA Student Council Elections 2025',
            description='The 2025 elections with expanded faculty representation.',
            start_date=now - timedelta(days=30),
            end_date=now - timedelta(days=23),
            is_active=False,
        )
        e2026 = Election.objects.create(
            title='CUEA Student Council Elections 2026',
            description='Upcoming elections. Cast your vote for student leaders!',
            start_date=now + timedelta(days=60),
            end_date=now + timedelta(days=67),
            is_active=True,
        )

        # ── Positions ─────────────────────────────────────────────
        def make_positions(election):
            Position.objects.create(election=election, title='President', max_votes=1, order=1)
            Position.objects.create(election=election, title='Vice President', max_votes=1, order=2)
            Position.objects.create(election=election, title='Secretary General', max_votes=1, order=3)
            Position.objects.create(election=election, title='Treasurer', max_votes=1, order=4)
            return list(Position.objects.filter(election=election).order_by('order'))

        pos_2024 = make_positions(e2024)
        pos_2025 = make_positions(e2025)
        pos_2026 = make_positions(e2026)

        # ── 10 Candidates ──────────────────────────────────────────
        self.stdout.write('Creating 10 candidates...')
        candidate_users = []
        for idx, (uname, pwd, first, last, school, bio) in enumerate(CANDIDATES_DATA):
            u = User(
                username=uname, password=hashed_cand_pwd, email=f'{uname}@cuea.edu',
                role='candidate', is_verified=True,
                student_id=f'{SCHOOL_ABBR[school]}-CAND/{idx+1:03d}',
                first_name=first, last_name=last,
            )
            candidate_users.append(u)
        
        # Save users first to get their IDs
        User.objects.bulk_create(candidate_users)
        saved_cand_users = {u.username: u for u in User.objects.filter(role='candidate')}

        candidates = []
        for idx, (uname, pwd, first, last, school, bio) in enumerate(CANDIDATES_DATA):
            u = saved_cand_users[uname]
            if idx < 3:
                election, positions = e2024, pos_2024
            elif idx < 6:
                election, positions = e2025, pos_2025
            else:
                election, positions = e2026, pos_2026

            pos = positions[idx % len(positions)]
            candidates.append(Candidate(
                user=u, position=pos, election=election,
                bio=bio, is_approved=True,
            ))
        Candidate.objects.bulk_create(candidates)
        
        # Re-fetch candidates with database IDs
        candidates = list(Candidate.objects.all())
        self.stdout.write(f'  Candidates: {len(candidates)}')

        # ── 50+ Manifestos ────────────────────────────────────────
        self.stdout.write('Creating 50 manifestos...')
        categories = list(MANIFESTO_TEMPLATES.keys())
        manifestos_batch = []

        for c in candidates:
            chosen_cats = random.choices(categories, k=5)
            for i, cat in enumerate(chosen_cats):
                templates = MANIFESTO_TEMPLATES[cat]
                title, desc = templates[i % len(templates)]
                manifestos_batch.append(Manifesto(
                    candidate=c, title=title, description=desc, category=cat
                ))
        Manifesto.objects.bulk_create(manifestos_batch)
        all_manifestos = list(Manifesto.objects.all())
        self.stdout.write(f'  Manifestos: {len(all_manifestos)}')

        # ── Votes from 600 voters on past elections ───────────────
        self.stdout.write('Casting votes from 600 voters...')
        all_voters = list(User.objects.filter(role='voter'))
        vote_batch = []

        for election, positions in [(e2024, pos_2024), (e2025, pos_2025)]:
            voter_subset = random.sample(all_voters, 500)
            for voter in voter_subset:
                for pos in positions:
                    pool = [c for c in candidates if c.position_id == pos.id and c.election_id == election.id]
                    if pool:
                        vote_batch.append(Vote(
                            voter=voter, candidate=random.choice(pool),
                            position=pos, election=election,
                            timestamp=election.start_date + timedelta(hours=random.randint(1, 167)),
                        ))
        Vote.objects.bulk_create(vote_batch, batch_size=500)
        self.stdout.write(f'  Votes Cast: {len(vote_batch)}')

        # ── Tracking updates: 70% completed ────────────────────────
        self.stdout.write('Creating tracking updates (70% completed)...')
        update_batch = []
        for manifesto in all_manifestos:
            for ui in range(random.randint(1, 3)):
                roll = random.random()
                if roll < 0.70:
                    status = 'completed'
                elif roll < 0.85:
                    status = 'in_progress'
                elif roll < 0.95:
                    status = 'delayed'
                else:
                    status = 'not_started'

                days_after = random.randint(30, 300)
                evidence = ''
                if status == 'completed' and random.random() > 0.3:
                    evidence = f'/candidate/manifestos/{manifesto.id}/updates/'

                update_batch.append(ManifestoUpdate(
                    manifesto=manifesto,
                    status=status,
                    description={
                        'completed': 'Fully delivered. Official report filed with the student council.',
                        'in_progress': 'Actively being worked on with visible progress.',
                        'delayed': 'Encountered administrative hurdles. Revised timeline in place.',
                        'not_started': 'Pending due to resource constraints.',
                    }[status],
                    evidence_url=evidence,
                    created_at=manifesto.candidate.election.end_date + timedelta(days=days_after),
                ))
        ManifestoUpdate.objects.bulk_create(update_batch)
        self.stdout.write(f'  Updates: {len(update_batch)}')

        # ── Ratings from voters on manifestos ─────────────────────
        self.stdout.write('Creating user ratings on manifestos...')
        rating_batch = []
        completed_manifesto_ids = set(
            u.manifesto_id for u in update_batch if u.status == 'completed'
        )

        for manifesto in all_manifestos:
            num_ratings = random.randint(10, 15)
            raters = random.sample(all_voters, min(num_ratings, len(all_voters)))
            for rater in raters:
                has_completed = manifesto.id in completed_manifesto_ids
                if has_completed:
                    rating = random.choices([4, 5, 3, 2], weights=[0.5, 0.3, 0.15, 0.05], k=1)[0]
                else:
                    rating = random.choices([2, 3, 1, 4], weights=[0.3, 0.4, 0.2, 0.1], k=1)[0]

                comments_pool = [
                    'Great work on this promise! Visible improvements on campus.',
                    'Still waiting to see more progress on this.',
                    'Excellent delivery. This has made a real difference for students.',
                    'Partially done but more needs to be accomplished.',
                    'Very impressed with the transparency and regular updates.',
                    'Could have been handled better. Needs more attention.',
                    'Outstanding commitment to this manifesto item!',
                    'Average progress. Room for improvement.',
                    'This was delivered exactly as promised. Thank you!',
                    'Good initiative but execution needs improvement.',
                ]
                comment = random.choice(comments_pool) if random.random() > 0.3 else ''

                rating_batch.append(ManifestoRating(
                    user=rater, manifesto=manifesto,
                    rating=rating, comment=comment,
                ))
        ManifestoRating.objects.bulk_create(rating_batch, batch_size=500)
        self.stdout.write(f'  Ratings: {len(rating_batch)}')

        # ── Audit logs ─────────────────────────────────────────────
        AuditLog.objects.create(
            user=User.objects.filter(is_superuser=True).first(),
            action='System initialized',
            details=f'Populated with {User.objects.count()} users, {Election.objects.count()} elections, {len(all_manifestos)} manifestos',
            ip_address='127.0.0.1',
        )

        # ── Summary ────────────────────────────────────────────────
        completed_manif = ManifestoUpdate.objects.filter(
            status='completed'
        ).values('manifesto').distinct().count()

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*50}\nCUEA DATA POPULATION COMPLETE\n{"="*50}\n'
            f'  Admins:       {User.objects.filter(role="admin").count()}\n'
            f'  Voters:       {User.objects.filter(role="voter").count()}\n'
            f'  Candidates:   {Candidate.objects.count()}\n'
            f'  Manifestos:   {len(all_manifestos)}\n'
            f'  Completed:    {completed_manif} ({round(completed_manif/len(all_manifestos)*100)}%)\n'
            f'  Ratings:      {ManifestoRating.objects.count()}\n'
            f'  Votes:        {Vote.objects.count()}\n'
            f'  Updates:      {ManifestoUpdate.objects.count()}\n'
            f'  Elections:    {Election.objects.count()}\n'
            f'\n'
            f'  Admin:  admin / admin123\n'
            f'  Voter:  v0001 / voter123 (thru v0600)\n'
            f'  Cand:   cand001 / cand123 (thru cand010)\n'
        ))
