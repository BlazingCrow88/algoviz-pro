"""
ASGI configuration for AlgoViz Pro.

ASGI (Asynchronous Server Gateway Interface) is the deployment interface
for async Django apps. We're not using async features yet, but this file
is required by Django for deployment.

For now, this is just standard Django setup - could add WebSocket support
later if we want real-time collaboration features.
"""

import os
from django.core.asgi import get_asgi_application

# Tell Django where our settings file is
# This needs to run before get_asgi_application() is called
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoviz_pro.settings')

# Create the ASGI application that web servers will use
application = get_asgi_application()