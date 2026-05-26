# Vercel serverless entry point for Django
# This file tells Vercel how to run our Django app.
# Vercel calls `app(environ, start_response)` for every HTTP request.

from django.core.wsgi import get_wsgi_application
import os, sys

# Add project root to Python path so Django can find settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evoting_project.settings')

app = get_wsgi_application()
