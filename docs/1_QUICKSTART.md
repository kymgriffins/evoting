# 🚀 QUICKSTART — Run the App in 30 Seconds

```bash
# 1. Go to the project folder
cd /home/gr8/Desktop/evoting

# 2. Activate the virtual environment (this loads Django)
source venv/bin/activate

# 3. Start the development server
python manage.py runserver

# 4. Open in your browser
#    http://localhost:8000
```

---

## First-Time Setup (only once)

```bash
cd /home/gr8/Desktop/evoting
source venv/bin/activate
python manage.py migrate        # creates the database tables
python manage.py populate_cuea  # fills in 600+ users and election data
python manage.py runserver      # start the server
```

---

## How to Stop the Server

Press `Ctrl + C` in the terminal where the server is running.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Command not found: python` | Use `python3` instead |
| `No module named django` | Run `pip install django djangorestframework` |
| `Port 8000 already in use` | Run `pkill -f manage.py` then try again |
| `Database has old data` | Run `python manage.py populate_cuea` to reset |
| `Migration errors` | Run `python manage.py migrate` |
