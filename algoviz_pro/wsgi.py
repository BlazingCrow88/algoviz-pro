"""
WSGI config for algoviz_pro project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Tell Django which settings file to use - this is important because Django needs to know
# where to find all the configuration before it can start serving pages
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoviz_pro.settings')

# This creates the actual WSGI application that web servers like Gunicorn or Apache use
# to communicate with Django. Even though I'm using the dev server for this project,
# this setup would be needed for production deployment
application = get_wsgi_application()