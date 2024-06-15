import os
import django

def init_test():
    if not os.environ.get('HAHA'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'efu_app.settings')
        django.setup()
