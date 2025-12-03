"""
WSGI configuration for AlgoViz Pro.

Standard Django WSGI setup for production deployment with servers
like Gunicorn or uWSGI.
"""

import os
from django.core.wsgi import get_wsgi_application

# Set Django settings module (must run before get_wsgi_application)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoviz_pro.settings')

application = get_wsgi_application()