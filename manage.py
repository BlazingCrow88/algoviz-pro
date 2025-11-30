#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Setting the default settings module so Django knows which config to use
    # This points to our project's settings.py - without this, Django wouldn't know
    # where to find database config, installed apps, etc.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoviz_pro.settings')

    try:
        # Import Django's command runner - this is what actually executes commands like
        # runserver, makemigrations, migrate, etc. when we type them in the terminal
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # If Django isn't installed, give a helpful error message instead of a cryptic one
        # The "forgot to activate a virtual environment" part is clutch because I've
        # definitely done that like 20 times and wondered why nothing worked lol
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Pass all the command-line arguments (like 'runserver' or 'migrate') to Django's handler
    # sys.argv contains everything we typed after 'python manage.py'
    execute_from_command_line(sys.argv)


# Standard Python idiom - only run main() if this file is executed directly,
# not if it's imported as a module somewhere else. This is the entry point
# for all Django management commands
if __name__ == '__main__':
    main()