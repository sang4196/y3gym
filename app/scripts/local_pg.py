"""Project-only PostgreSQL lifecycle. No sudo, TCP, passwords or system service."""
import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parents[1]
RUNTIME = BASE / '.runtime'
ROOT = RUNTIME / 'pg-root'
BIN = ROOT / 'usr/lib/postgresql/18/bin'
DATA = RUNTIME / 'pg-data'
SOCKET = RUNTIME / 'pg-socket'
PORT = '55432'
ENV = os.environ.copy()
ENV['LD_LIBRARY_PATH'] = str(ROOT / 'usr/lib/x86_64-linux-gnu')

def run(name, *args, **kwargs):
    return subprocess.run([str(BIN / name), *map(str, args)], env=ENV, check=True, **kwargs)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['init', 'start', 'stop', 'status'])
    action = parser.parse_args().action
    SOCKET.mkdir(mode=0o700, parents=True, exist_ok=True)
    if action == 'init':
        if DATA.exists():
            raise SystemExit('Existing cluster preserved; init refused.')
        run('initdb', '-D', DATA, '-U', 'y3gym_owner', '--auth-local=peer', '--auth-host=reject', '--encoding=UTF8', '--locale=C.UTF-8')
        # Peer mappings are confined to a 0700 socket owned by the current OS user.
        user = getpass.getuser()
        if not user.replace('_', '').replace('-', '').isalnum():
            raise SystemExit('Unsupported OS account name')
        (DATA / 'pg_ident.conf').write_text('\n'.join(f'y3gym {user} {role}' for role in ['y3gym_owner', 'y3gym_dev', 'y3gym_test'])+'\n')
        (DATA / 'pg_hba.conf').write_text('local all y3gym_owner peer map=y3gym\nlocal y3gym_dev y3gym_dev peer map=y3gym\nlocal all y3gym_test peer map=y3gym\nlocal all all reject\nhost all all 0.0.0.0/0 reject\nhost all all ::/0 reject\n')
        with (DATA / 'postgresql.conf').open('a') as f:
            f.write(f"\nlisten_addresses = ''\nport = {PORT}\nunix_socket_directories = '{SOCKET}'\nunix_socket_permissions = 0700\njit = off\n")
        start()
        sql = 'CREATE ROLE y3gym_dev LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE; CREATE ROLE y3gym_test LOGIN NOSUPERUSER CREATEDB NOCREATEROLE; CREATE DATABASE y3gym_dev OWNER y3gym_dev;'
        for statement in sql.split(';'):
            if statement.strip():
                run('psql', '-h', SOCKET, '-p', PORT, '-U', 'y3gym_owner', '-d', 'postgres', '-v', 'ON_ERROR_STOP=1', '-c', statement)
        run('psql', '-h', SOCKET, '-p', PORT, '-U', 'y3gym_owner', '-d', 'postgres', '-v', 'ON_ERROR_STOP=1', '-c', 'REVOKE CONNECT ON DATABASE y3gym_dev FROM PUBLIC; GRANT CONNECT ON DATABASE y3gym_dev TO y3gym_dev;')
    elif action == 'start':
        start()
    else:
        run('pg_ctl', '-D', DATA, *(['-m', 'fast', '-w', 'stop'] if action == 'stop' else ['status']))

def start():
    log = RUNTIME / ('postgres-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.log')
    log.touch(exist_ok=False)
    run('pg_ctl', '-D', DATA, '-l', log, '-w', 'start')

if __name__ == '__main__':
    main()
