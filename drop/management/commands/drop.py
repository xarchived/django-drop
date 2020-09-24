import glob
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Clean all migration files and recreate schema'

    def _drop_postgres(self):
        try:
            import psycopg2
        except ImportError:
            raise CommandError('Package not found (psycopg2)')

        con = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database=settings.DATABASES['default']['NAME'])

        with con.cursor() as cur:
            cur.execute('drop schema if exists public cascade')
        con.commit()

        self.stdout.write(self.style.SUCCESS(f'Successfully dropped public schema of PostgreSQL database'))

    def _drop_sqlite(self):
        db_file = settings.DATABASES['default']['NAME']
        if os.path.isfile(db_file):
            os.remove(db_file)
            self.stdout.write(self.style.SUCCESS('Successfully deleted SQLite db file'))
        else:
            self.stdout.write(self.style.WARNING('No SQLite file is found'))

    def _remove_migrations_files(self):
        paths = []
        for app in settings.INSTALLED_APPS:
            try:
                module_ = __import__(app)
            except ImportError:
                raise CommandError(f'Could not import app ({app})')

            paths += module_.__path__

        self.stdout.write(self.style.MIGRATE_HEADING('Removing migrations:'))

        deleted = False
        for path in paths:
            files = glob.glob(f'{path}/migrations/*')
            for f in files:
                if '__init__.py' in f:
                    continue

                self.stdout.write(self.style.HTTP_SUCCESS(f'  Removing {f}...'), ending='')
                deleted = True

                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)

                self.stdout.write(self.style.SUCCESS(' OK'))

        if not deleted:
            self.stdout.write(self.style.HTTP_SUCCESS('  No migrations to delete'))

    def handle(self, *args, **options):
        engine = settings.DATABASES['default']['ENGINE']
        if engine == 'django.db.backends.postgresql_psycopg2':
            self._drop_postgres()
        elif engine == 'django.db.backends.sqlite3':
            self._drop_sqlite()
        else:
            raise CommandError(f'Engine not supported ({engine})')

        self._remove_migrations_files()
