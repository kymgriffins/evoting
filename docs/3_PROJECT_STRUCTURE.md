# 📁 PROJECT STRUCTURE — Every File Explained

```
evoting/                          # ROOT FOLDER (this is your project)
│
├── manage.py                     # 🎯 Django's command center. Run ALL commands through this.
│                                   #   python manage.py runserver  → starts the web server
│                                   #   python manage.py migrate    → updates database
│                                   #   python manage.py populate_cuea → fills test data
│
├── db.sqlite3                    # 💾 The database file (SQLite). All users, votes, etc live here.
│                                   #   No need to install PostgreSQL — SQLite is built-in.
│
├── venv/                         # 🔒 Virtual Environment. Isolates Python packages so they
│                                   #   don't conflict with your system. Contains Django itself.
│                                   #   Activate with: source venv/bin/activate
│
├── docs/                         # 📖 YOU ARE HERE — all documentation
│   ├── 1_QUICKSTART.md
│   ├── 2_CREDENTIALS.md
│   ├── 3_PROJECT_STRUCTURE.md    ← this file
│   ├── 4_DJANGO_FOR_NEWBIES.md
│   ├── 5_API_REFERENCE.md
│   ├── 6_USER_GUIDE.md
│   └── 7_DATA_MODEL.md
│
├── evoting_project/              # 🏗️ DJANGO PROJECT SETTINGS (the skeleton)
│   ├── __init__.py               #     (empty — tells Python this is a package)
│   ├── settings.py               # ⚙️ MAIN SETTINGS: database, installed apps, timezone, etc
│   ├── urls.py                   # 🧭 MASTER URL ROUTER: maps all web addresses to code
│   ├── asgi.py                   #     (for advanced deployment — ignore for now)
│   └── wsgi.py                   #     (for production deployment — ignore for now)
│
└── core/                         # 💡 THE MAIN APP — all your code lives here
    │
    ├── __init__.py               #     (empty)
    ├── admin.py                  # 🔧 Django Admin panel configuration
    ├── apps.py                   #     (app config — rarely touched)
    ├── models.py                 # 🗃️ DATABASE MODELS: defines all tables (User, Election, Vote, etc)
    ├── forms.py                  # 📝 FORM DEFINITIONS: login form, registration form, etc
    ├── serializers.py            # 🔄 API SERIALIZERS: converts database data to JSON for APIs
    ├── views.py                  # 🎮 VIEWS (THE BRAIN): all the logic — login, voting, tracking, APIs
    ├── api_urls.py               # 🌐 API URL ROUTES: maps /api/... to API views
    │
    ├── urls.py                   #     (NOT USED — we put URLs in evoting_project/urls.py instead)
    ├── tests.py                  #     (empty — add tests here later)
    │
    ├── management/               # 📦 CUSTOM COMMANDS
    │   └── commands/
    │       └── populate_cuea.py  #     python manage.py populate_cuea → fills test data
    │
    ├── templates/                # 🎨 HTML TEMPLATES (the visual layer)
    │   │
    │   ├── core/                 #     HTML pages for the app
    │   │   ├── base.html         #     🏠 BASE TEMPLATE: nav bar, footer, styles — every page uses this
    │   │   ├── home.html         #     🏁 Homepage / landing page
    │   │   ├── dashboard.html    #     📊 Role-based dashboard (different for admin/voter/candidate)
    │   │   ├── vote.html         #     🗳️ Voting page (lists candidates per position)
    │   │   ├── results.html      #     📈 Election results page
    │   │   ├── leaderboard.html  #     🏆 Candidate performance leaderboard
    │   │   ├── manifesto_tracking.html  # 📋 Tracking dashboard with ratings
    │   │   ├── manifesto_list.html      # 📄 Candidate's list of their own manifestos
    │   │   ├── manifesto_form.html      # ✏️ Form to create/edit a manifesto
    │   │   ├── manifesto_updates.html   # 📝 Manifesto detail page with updates & ratings
    │   │   ├── candidate_setup.html     # 👤 Candidate registration form
    │   │   ├── admin_elections.html     # 🏛️ Admin: manage elections
    │   │   ├── admin_positions.html     # 🏛️ Admin: manage positions
    │   │   ├── admin_candidates.html    # 🏛️ Admin: approve/reject candidates
    │   │   └── admin_audit.html         # 📋 Admin: view audit logs
    │   │
    │   └── registration/          #     Django auth templates
    │       ├── login.html         #     🔑 Login page
    │       └── register.html      #     📝 Registration page
    │
    └── static/
        └── core/
            └── css/              #     (currently unused — styles are inline in base.html)
```

---

## 🔄 How Django Files Connect (data flow)

```
INTERNET  ←→  urls.py  ←→  views.py  ←→  models.py  ←→  SQLite database
                          ↕                ↕
                     templates/        forms.py
                     (HTML pages)      (form validation)
                          ↕
                     serializers.py
                     (JSON APIs)
```

**Example — A user votes:**

1. User clicks "Submit Votes" on `vote.html`
2. Browser sends POST to `/vote/1/`
3. `urls.py` maps this to `views.vote_page`
4. `views.vote_page` creates a `Vote` object in models
5. Vote is saved to `db.sqlite3`
6. User is redirected to dashboard

---

## 🔑 Key Files to Know

| File | What it does |
|------|-------------|
| `models.py` | Defines 9 database tables (User, Election, Position, Candidate, Manifesto, Vote, ManifestoUpdate, ManifestoRating, AuditLog) |
| `views.py` | Contains ALL the logic — 25+ functions that handle every page request |
| `templates/core/*.html` | 15 HTML pages that the user sees |
| `evoting_project/settings.py` | Configuration: database, timezone, installed apps |
| `evoting_project/urls.py` | Master URL map — connects every web address to a view function |
| `core/api_urls.py` | API routes — connects `/api/...` to API view functions |

---

## 📐 Architecture Pattern

This app uses **MVT** (Model-View-Template) — Django's version of MVC:

| Layer | Role | Files |
|-------|------|-------|
| **Model** | Database structure | `models.py` |
| **View** | Business logic | `views.py` |
| **Template** | User interface | `templates/*.html` |
| **URL** | Routing | `urls.py` |
