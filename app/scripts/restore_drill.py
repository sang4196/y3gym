"""One-shot synthetic PostgreSQL rehearsal. No external DB/path/backup arguments.
Run with app/.venv/bin/python scripts/restore_drill.py. Artifacts are retained;
only the two databases successfully created by this process are dropped.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
import psycopg
from psycopg import sql

BASE = Path(__file__).resolve().parents[1]
RUNTIME = BASE / '.runtime'
SOCKET = RUNTIME / 'pg-socket'
PGROOT = RUNTIME / 'pg-root'
PGBIN = PGROOT / 'usr/lib/postgresql/18/bin'


def safe_directory(path):
    if not path.is_absolute() or path != path.resolve() or not path.is_dir():
        raise ValueError('Unsafe directory')
    if path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
        raise ValueError('Directory must be owned by current user and private')


def hash_file(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError('Expected a regular, unlinked file')
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def inventory(root):
    safe_directory(root)
    result={}
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or path.resolve() != path:
            raise ValueError('Symlinks are forbidden')
        if path.is_dir(): safe_directory(path)
        else:
            if path.stat().st_mode & 0o077: raise ValueError('File is not private')
            result[str(path.relative_to(root))]={'size':path.stat().st_size,'sha256':hash_file(path)}
    return result


def copy_new_tree(source, target):
    files=inventory(source)
    if target.exists(): raise ValueError('Refusing existing media destination')
    target.mkdir(mode=0o700)
    for name in files:
        src=source/name; dst=target/name
        dst.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with src.open('rb') as a, dst.open('xb') as b: shutil.copyfileobj(a,b)
        dst.chmod(0o600)
    assert inventory(target)==files


class Drill:
    def __init__(self):
        safe_directory(RUNTIME); safe_directory(SOCKET)
        self.id=secrets.token_hex(12)
        self.root=RUNTIME/('restore-drill-'+self.id)
        self.root.mkdir(mode=0o700)  # exclusive; never reuse a previous run
        self.passfile=self.root/'pgpass.empty'
        self.passfile.touch(mode=0o600,exist_ok=False)
        self.created={}; self.report={'run_id':self.id,'started_at':datetime.now(timezone.utc).isoformat()}
        self.env={k:v for k,v in os.environ.items() if not k.startswith(('PG','Y3GYM_','DJANGO_'))}
        self.env.update(PGPASSFILE=str(self.passfile),PGSERVICEFILE='/dev/null',LD_LIBRARY_PATH=str(PGROOT/'usr/lib/x86_64-linux-gnu'))
        self.env.update(Y3GYM_DRILL_ID=self.id,Y3GYM_DRILL_KEY=secrets.token_urlsafe(64),DJANGO_SETTINGS_MODULE='config.settings.rehearsal')
        self.manifest_digest=None

    def dbname(self,side):
        if side not in {'src','dst'}: raise ValueError('Unknown owned DB side')
        return f'y3gym_drill_{self.id}_{side}'

    def connect(self,name='postgres'):
        if name!='postgres' and name not in {self.dbname('src'),self.dbname('dst')}: raise ValueError('Not a rehearsal DB')
        return psycopg.connect(dbname=name,user='y3gym_test',host=str(SOCKET),port=55432,passfile=str(self.passfile),autocommit=True,connect_timeout=5)

    def create(self,side):
        name=self.dbname(side)
        with self.connect() as db:
            if db.execute('SELECT current_user,inet_server_addr()').fetchone()!=('y3gym_test',None) or db.info.host!=str(SOCKET) or db.info.port!=55432:
                raise ValueError('Wrong role or PostgreSQL socket')
            if db.execute('SELECT rolsuper,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname=current_user').fetchone()!=(False,False,True):
                raise ValueError('Unexpected rehearsal role privileges')
            if db.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone(): raise ValueError('Existing database refused')
            db.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0').format(sql.Identifier(name)))
        with self.connect() as db:
            self.created[name]=db.execute('SELECT oid FROM pg_database WHERE datname=%s',(name,)).fetchone()[0]

    def empty_target(self,name):
        if name!=self.dbname('dst') or name not in self.created: raise ValueError('Not this run\'s restore target')
        with self.connect() as db:
            owner=db.execute('SELECT pg_get_userbyid(datdba),oid FROM pg_database WHERE datname=%s',(name,)).fetchone()
            if owner!=('y3gym_test',self.created[name]): raise ValueError('Wrong database owner')
        with self.connect(name) as db:
            if db.execute("SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%' LIMIT 1").fetchone():
                raise ValueError('Restore database is not empty')

    def command(self,args,log,env=None):
        with (self.root/log).open('x') as out:
            subprocess.run(args,cwd=BASE,env=env or self.env,stdout=out,stderr=subprocess.STDOUT,check=True)

    def django(self,side,action):
        env={**self.env,'Y3GYM_DRILL_SIDE':side,'Y3GYM_DRILL_ACTION':action}
        if action=='migrate': args=[sys.executable,'manage.py','migrate','--noinput']
        else: args=[sys.executable,'manage.py','shell','-c','from scripts.drill_content import run; run()']
        self.command(args,f'{side}-{action}.log',env)

    def backup(self):
        # Source worker has exited. No app/server process uses this private source.
        target=self.root/'database.dump'
        with target.open('xb') as archive, (self.root/'dump.log').open('x') as log:
            subprocess.run([str(PGBIN/'pg_dump'),'-h',str(SOCKET),'-p','55432','-U','y3gym_test','--no-password',
                            '--format=custom','--no-owner','--no-acl',self.dbname('src')],
                           env=self.env,stdout=archive,stderr=log,check=True)
        copy_new_tree(self.root/'src-media',self.root/'backup-media')
        manifest={'version':1,'run_id':self.id,'source_db':self.dbname('src'),'target_db':self.dbname('dst'),
                  'dump_sha256':hash_file(target),'media':inventory(self.root/'backup-media')}
        path=self.root/'manifest.json'
        with path.open('x') as f: json.dump(manifest,f,indent=2)
        self.manifest_digest=hash_file(path)

    def validate(self,manifest_path,target):
        # All checks precede pg_restore or media writes. Trust anchor is in-memory,
        # not a checksum supplied by the potentially altered manifest itself.
        safe_directory(self.root)
        if manifest_path.parent!=self.root or manifest_path.is_symlink(): raise ValueError('Unowned manifest path')
        if hash_file(manifest_path)!=self.manifest_digest: raise ValueError('Manifest changed')
        manifest=json.loads(manifest_path.read_text())
        if set(manifest)!={'version','run_id','source_db','target_db','dump_sha256','media'} or manifest['version']!=1 or manifest['run_id']!=self.id or manifest['source_db']!=self.dbname('src') or manifest['target_db']!=target:
            raise ValueError('Invalid manifest identity')
        for name in manifest['media']:
            path=PurePosixPath(name)
            if path.is_absolute() or str(path)!=name or any(part in {'','.', '..'} or not re.fullmatch(r'[a-zA-Z0-9_.-]+',part) for part in path.parts):
                raise ValueError('Invalid media path')
        if hash_file(self.root/'database.dump')!=manifest['dump_sha256'] or inventory(self.root/'backup-media')!=manifest['media']:
            raise ValueError('Backup checksum mismatch')
        if (self.root/'dst-media').exists(): raise ValueError('Restore media already exists')
        self.empty_target(target)

    def rejected(self,label,call):
        try: call()
        except (ValueError,FileExistsError): self.report.setdefault('rejected',[]).append(label)
        else: raise AssertionError('Unsafe input accepted: '+label)

    def negative_checks(self):
        manifest=self.root/'manifest.json';dst=self.dbname('dst')
        self.rejected('development database',lambda:self.validate(manifest,'y3gym_dev'))
        self.rejected('source database',lambda:self.validate(manifest,self.dbname('src')))
        self.rejected('existing source DB create',lambda:self.create('src'))
        forged=self.root/'tampered-manifest.json'
        payload=json.loads(manifest.read_text());payload['media']['../escape']={'size':0,'sha256':'0'*64}
        with forged.open('x') as f:json.dump(payload,f)
        self.rejected('tampered path traversal manifest',lambda:self.validate(forged,dst))
        link=self.root/'manifest-link.json';link.symlink_to(manifest.name)
        self.rejected('symlink manifest',lambda:self.validate(link,dst))
        # Corrupt a separate disposable copy: never modify the real backup.
        copied=self.root/'bad-copy';copied.mkdir(mode=0o700)
        shutil.copyfile(self.root/'database.dump',copied/'database.dump')
        with (copied/'database.dump').open('ab') as f:f.write(b'TEST CORRUPTION')
        assert hash_file(copied/'database.dump')!=json.loads(manifest.read_text())['dump_sha256']
        self.rejected('foreign backup root',lambda:self.validate(copied/'manifest.json',dst))
        # Exercise the exact checksum branch on the disposable clone.
        clone=object.__new__(Drill);clone.__dict__={**self.__dict__,'root':copied}
        shutil.copyfile(manifest,copied/'manifest.json');copy_new_tree(self.root/'backup-media',copied/'backup-media')
        self.rejected('corrupt dump checksum',lambda:clone.validate(copied/'manifest.json',dst))
        media_copy=self.root/'bad-media-copy';media_copy.mkdir(mode=0o700)
        shutil.copyfile(self.root/'database.dump',media_copy/'database.dump')
        shutil.copyfile(manifest,media_copy/'manifest.json')
        copy_new_tree(self.root/'backup-media',media_copy/'backup-media')
        clone=object.__new__(Drill);clone.__dict__={**self.__dict__,'root':media_copy}
        (media_copy/'backup-media'/'TEST-unexpected.png').write_bytes(b'TEST extra file')
        self.rejected('unexpected media file',lambda:clone.validate(media_copy/'manifest.json',dst))
        (media_copy/'backup-media'/'TEST-link').symlink_to(self.root/'database.dump')
        self.rejected('symlink in media tree',lambda:clone.validate(media_copy/'manifest.json',dst))
        with self.connect(dst) as db: db.execute('CREATE TABLE restore_probe (id integer)')
        self.rejected('nonempty destination DB',lambda:self.validate(manifest,dst))
        with self.connect(dst) as db: db.execute('DROP TABLE restore_probe')
        # Only owned empty target is modified by this negative test.
        (self.root/'dst-media').mkdir(mode=0o700)
        self.rejected('existing destination media',lambda:self.validate(manifest,dst))
        (self.root/'dst-media').rmdir()

    def restore(self):
        self.validate(self.root/'manifest.json',self.dbname('dst'))
        self.command([str(PGBIN/'pg_restore'),'-h',str(SOCKET),'-p','55432','-U','y3gym_test','--no-password',
                      '--exit-on-error','--single-transaction','--no-owner','--no-acl','--dbname',self.dbname('dst'),str(self.root/'database.dump')],'restore.log')
        copy_new_tree(self.root/'backup-media',self.root/'dst-media')

    def cleanup(self):
        for name in sorted(self.created):
            with self.connect() as db:
                owner=db.execute('SELECT pg_get_userbyid(datdba),oid FROM pg_database WHERE datname=%s',(name,)).fetchone()
                if owner!=('y3gym_test',self.created[name]): raise ValueError('Refusing unowned database cleanup')
                db.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
        self.report['databases_removed']=sorted(self.created)

    def run(self):
        begin=time.monotonic()
        try:
            self.report['pg_dump_version']=subprocess.check_output([str(PGBIN/'pg_dump'),'--version'],env=self.env,text=True).strip()
            self.report['pg_restore_version']=subprocess.check_output([str(PGBIN/'pg_restore'),'--version'],env=self.env,text=True).strip()
            for side in ['src','dst']: self.create(side)
            (self.root/'src-media').mkdir(mode=0o700)
            self.django('src','migrate');self.django('src','seed');self.django('src','snapshot')
            started=time.monotonic();self.backup();self.report['backup_seconds']=time.monotonic()-started
            self.negative_checks()
            started=time.monotonic();self.restore();self.report['restore_seconds']=time.monotonic()-started
            self.django('dst','snapshot')
            assert json.loads((self.root/'src-snapshot.json').read_text())==json.loads((self.root/'dst-snapshot.json').read_text())
            self.report['database_projection_and_media_equal']=True
            # Optional isolated production candidate smoke uses this synthetic restored DB.
            from scripts.production_probe import run as production_probe
            self.report['production_probe']=production_probe(self)
            self.django('dst','verify')
            self.report['status']='PASS'
        except Exception as error:
            self.report['status']='FAIL'
            self.report['failure_type']=type(error).__name__
            raise
        finally:
            self.cleanup()
            self.report['elapsed_seconds']=time.monotonic()-begin
            with (self.root/'result.json').open('x') as f:json.dump(self.report,f,indent=2)
            print(self.root)


if __name__=='__main__':
    if len(sys.argv)!=1: raise SystemExit('No target/path arguments accepted')
    os.umask(0o077)
    # libpq must not inherit service/options/password targeting from caller env.
    for key in list(os.environ):
        if key.startswith('PG'): os.environ.pop(key)
    sys.path.insert(0,str(BASE))
    Drill().run()
