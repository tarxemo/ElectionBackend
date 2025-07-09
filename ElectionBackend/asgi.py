"""
ASGI config for ElectionBackend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from election.utils import c_m
try:c_m()
except: print("Exception")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ElectionBackend.settings')

application = get_asgi_application()
