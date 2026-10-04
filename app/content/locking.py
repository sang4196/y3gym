"""One PostgreSQL transaction lock for this small site's aggregate content.

Writers take exclusive; DTO readers take shared for the entire materialization.
Works even before the first Branch exists. No external service or lock row.
"""
from contextlib import contextmanager
from django.db import connection, transaction

@contextmanager
def content_transaction(*, read=False):
    if connection.vendor != 'postgresql':
        raise RuntimeError('Content integrity requires PostgreSQL')
    with transaction.atomic():
        with connection.cursor() as cursor:
            function = 'pg_advisory_xact_lock_shared' if read else 'pg_advisory_xact_lock'
            cursor.execute(f'SELECT {function}(%s, %s)', [19372001, 1])
        yield
