"""
WSGI config for grammarexpert project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

# sys.path.append("/home/abhinav/grammar/GrammarExpert/venv/lib/site-packages")

from django.core.wsgi import get_wsgi_application

# sys.path.append("F:/Projects/GrammarExpert/venv/Lib/site-packages")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grammarexpert.settings')

application = get_wsgi_application()
