import sys
import os
import django
from django.test.runner import DiscoverRunner
from django.conf import settings

def execute_tests():
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'efu_app.settings')
        django.setup()
    except Exception as e:
        print(f'{type(e).__name__} {e}')
        return


    test_runner = DiscoverRunner()

    try:
        failures = test_runner.run_tests(['efu_engine'])
        if failures:
            print(f'{failures}')
        # sys.exit(bool(failures))
    except Exception as e:
        print(f'{type(e).__name__} {e}')


if __name__ == '__main__':
    execute_tests()