"""
ASGI config for mimic_explorer project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimic_explorer.settings')

application = get_asgi_application()
