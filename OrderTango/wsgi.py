"""
WSGI config for OrderTango project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os,sys

from django.core.wsgi import get_wsgi_application

path='/var/www/ordertango'

sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OrderTango.settings')

application = get_wsgi_application()