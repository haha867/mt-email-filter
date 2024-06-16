import time
import datetime as dt

from psycopg2 import OperationalError as Psycopg2OpError

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for database."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write('Waiting for database...')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OpError, OperationalError) as e:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
            #except OperationalError as e:
            #    self.stdout.write(f'{dt.datetime.now().strftime("%Y-%m-%d.%H:%M:%S.%f")} OperationalError {e} OperationalError Database unavailable, waiting 1 second...')
            #    time.sleep(1)
            #    #continue
            #except Psycopg2OpError as e:
            #    self.stdout.write(f'{dt.datetime.now().strftime("%Y-%m-%d.%H:%M:%S.%f")} Psycopg2OpError{e} Database unavailable, waiting 1 second...')
            #    time.sleep(1)
            #    #continue

        #self.stdout.write(self.style.SUCCESS(f'{dt.datetime.now().strftime("%Y-%m-%d.%H:%M:%S.%f")} Database available!'))
        self.stdout.write(self.style.SUCCESS('Database available!'))