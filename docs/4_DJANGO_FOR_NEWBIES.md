# 🐍 DJANGO FOR NEWBIES — How This All Works

## What is Django?

Django is a Python framework that builds web apps. Think of it as a factory that gives you all the machines needed to build a website — you just need to put the pieces together.

---

## How a Web Request Flows (in simple terms)

```
You type URL          Django finds          Python function      Returns HTML
in browser            the right view        runs your logic      page to browser
     │                      │                     │                    │
     ▼                      ▼                     ▼                    ▼
  /vote/1/    ───►   urls.py maps it    ───►   views.vote_page()   ──►  vote.html
                     to vote_page()             gets candidates           (your ballot)
                                                checks if user
                                                already voted
```

**Think of it like a restaurant:**
- `urls.py` = the **menu** (lists what's available)
- `views.py` = the **kitchen** (where the cooking happens)
- `templates/` = the **plating** (how food looks to customer)
- `models.py` = the **pantry** (where ingredients are stored)

---

## 🏗️ The 4 Essential Files You Need to Know

### 1. `models.py` — The Database Schema

Defines what data you store. Each **class** = one **database table**.

```python
# models.py example
class Student(models.Model):
    name = models.CharField(max_length=100)  # text column
    age = models.IntegerField()              # number column
    enrolled = models.BooleanField(default=True)  # yes/no
```

**Key rule:** Every time you change `models.py`, run:
```bash
python manage.py makemigrations   # "take a snapshot of my changes"
python manage.py migrate          # "apply those changes to the database"
```

---

### 2. `views.py` — The Brain

Each **function** handles one page. It fetches data from models and passes it to templates.

```python
# views.py example
def student_list(request):
    students = Student.objects.all()           # get all students from DB
    return render(request, 'list.html', {      # send to HTML template
        'students': students                   # available in template as {{ students }}
    })
```

**Two types of views in our app:**
- **Regular views** — return HTML pages (for humans)
- **API views** — return JSON (for other apps/programs)

---

### 3. `urls.py` — The Address Book

Maps URLs to functions.

```python
# urls.py
from . import views

urlpatterns = [
    path('students/', views.student_list),          # /students/ calls student_list()
    path('students/<int:id>/', views.student_detail),  # /students/5/ calls student_detail(id=5)
]
```

---

### 4. Templates (HTML) — What Users See

Django templates are HTML with special markers:

| Syntax | What it does | Example |
|--------|-------------|---------|
| `{{ variable }}` | Prints a value | `Hello {{ user.name }}` |
| `{% for x in list %}` | Loops | `{% for s in students %}...{% endfor %}` |
| `{% if condition %}` | Conditional | `{% if user.role == 'admin' %}...{% endif %}` |
| `{% url 'name' %}` | Generates URL | `<a href="{% url 'dashboard' %}">` |
| `{% extends "base.html" %}` | Inherits layout | Reuses nav bar and footer |

**Our templates inherit from `base.html`** — so every page automatically has the nav bar, styles, and footer. We only write the content section in each page.

---

## 🔐 How Authentication Works (Login/Register)

Django provides built-in auth. We customized it:

1. **Register** → `UserRegisterForm` creates a new user with a role (voter/candidate)
2. **Login** → Django checks username + password, creates a session
3. **Session** → Browser stores a cookie so Django recognizes you on next request
4. **Logout** → Deletes the session cookie

**In views:** `@login_required` checks if user is logged in before showing a page.

**In templates:** `{{ user }}` is always available. `{{ user.role }}` tells us what type of user.

---

## 🎭 Role-Based Access (3 User Types)

Our app has 3 roles. Each sees a different dashboard:

```python
if user.role == 'admin':
    return render(request, 'dashboard.html', {'section': 'admin', ...})
elif user.role == 'candidate':
    return render(request, 'dashboard.html', {'section': 'candidate', ...})
else:  # voter
    return render(request, 'dashboard.html', {'section': 'voter', ...})
```

---

## 🔄 The Request-Response Cycle (Complete Example)

When a **voter** clicks "Cast Your Vote":

```
1. Click button on /vote/1/
        │
2. Browser sends POST request to server
        │
3. urls.py matches:  path('vote/<int:election_id>/', views.vote_page)
        │
4. views.vote_page(request, election_id=1) runs:
        │
5. ┌── Fetches election from database
   │   Fetches positions for that election
   │   Fetches candidates for each position
   │   Checks if user already voted (prevents double voting)
   │── Saves vote to database
   │   Creates AuditLog entry
   │   Redirects to dashboard
        │
6. Browser shows dashboard with success message
```

---

## 🐞 Common Commands You'll Use

```bash
source venv/bin/activate          # Activate virtual environment (do this first!)
python manage.py runserver        # Start the dev server
python manage.py migrate          # Apply database changes
python manage.py makemigrations   # Create database change files
python manage.py createsuperuser  # Create admin account
python manage.py populate_cuea    # Fill database with test data
python manage.py shell            # Interactive Python shell (for testing)
python manage.py dbshell          # Direct database access (SQL commands)
```

---

## 📄 Quick Reference — Django Template Tags

```html
{# This is a comment #}

<!-- Variables -->
<h1>{{ title }}</h1>
<p>{{ user.get_full_name|default:"Guest" }}</p>  <!-- |default: = fallback if empty -->

<!-- For Loops -->
{% for candidate in candidates %}
  <li>{{ candidate.name }} - {{ candidate.votes }} votes</li>
{% empty %}
  <li>No candidates</li>
{% endfor %}

<!-- If/Else -->
{% if user.role == 'admin' %}
  <a href="/admin/">Admin Panel</a>
{% elif user.role == 'candidate' %}
  <a href="/manifestos/">My Manifestos</a>
{% else %}
  <a href="/vote/">Vote</a>
{% endif %}

<!-- URLs (always use this instead of hardcoding) -->
<a href="{% url 'dashboard' %}">Dashboard</a>
<a href="{% url 'vote' election.id %}">Vote</a>  <!-- passes election.id as argument -->

<!-- Static files -->
<link rel="stylesheet" href="{% static 'core/css/style.css' %}">
```
