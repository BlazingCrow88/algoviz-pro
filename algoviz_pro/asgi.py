"""
ASGI configuration for AlgoViz Pro.

Standard Django ASGI setup. Not using async features currently but file
is required for deployment.
"""

import os
from django.core.asgi import get_asgi_application

# Set Django settings module (must run before get_asgi_application)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoviz_pro.settings')

# ASGI application for web servers
application = get_asgi_application()