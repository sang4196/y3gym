"""Isolated production-candidate checks; no real environment files or credentials."""
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from scripts.restore_drill import BASE, SOCKET


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


def request(port,path,*,host='gym.invalid',forwarded=False,method='GET',body=None):
    headers={'Host':host}
    if forwarded: headers['X-Forwarded-Proto']='https'
    req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,headers=headers,method=method,data=body)
    opener=urllib.request.build_opener(NoRedirect)
    try:response=opener.open(req,timeout=10)
    except urllib.error.HTTPError as error:response=error
    with response:return response.status,dict(response.headers),response.read()


def run(drill):
    root=Path(tempfile.mkdtemp(prefix='y3gym-production-probe-'));root.chmod(0o700)
    for name in ['media','static','tmp']:(root/name).mkdir(mode=0o700)
    # Copy only this run's synthetic restore media, never the dev media tree.
    from scripts.restore_drill import inventory
    import shutil
    for name in inventory(drill.root/'dst-media'):
        dest=root/'media'/name;dest.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with (drill.root/'dst-media'/name).open('rb') as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst)
    env={k:v for k,v in drill.env.items() if not k.startswith(('Y3GYM_','DJANGO_','GUNICORN_'))}
    env.update(DJANGO_SETTINGS_MODULE='config.settings.production',Y3GYM_SECRET_KEY=secrets.token_urlsafe(64),
               Y3GYM_ALLOWED_HOSTS='gym.invalid',Y3GYM_PUBLIC_ORIGIN='https://gym.invalid',
               Y3GYM_MEDIA_ROOT=str(root/'media'),Y3GYM_STATIC_ROOT=str(root/'static'),Y3GYM_UPLOAD_TMP=str(root/'tmp'),
               Y3GYM_DB_NAME=drill.dbname('dst'),Y3GYM_DB_USER='y3gym_test',Y3GYM_DB_HOST=str(SOCKET),Y3GYM_DB_PORT='55432')
    result={'synthetic_storage':str(root),'negative_settings':[],'http_checks':[]}
    # Each settings case is a fresh process; error logs never include env values.
    script="from config.settings import production; print('SETTINGS_OK')"
    invalid={
      'missing key':{'Y3GYM_SECRET_KEY':None},'short key':{'Y3GYM_SECRET_KEY':'short'},
      'wildcard host':{'Y3GYM_ALLOWED_HOSTS':'*'},'localhost':{'Y3GYM_ALLOWED_HOSTS':'localhost'},
      'HTTP origin':{'Y3GYM_PUBLIC_ORIGIN':'http://gym.invalid'},'unallowed origin':{'Y3GYM_PUBLIC_ORIGIN':'https://other.invalid'},
      'missing database':{'Y3GYM_DB_NAME':None},'development database':{'Y3GYM_DB_NAME':'y3gym_dev'},
      'owner role':{'Y3GYM_DB_USER':'y3gym_owner'},'invalid DB port':{'Y3GYM_DB_PORT':'0'},
      'missing media':{'Y3GYM_MEDIA_ROOT':None},'development media':{'Y3GYM_MEDIA_ROOT':str(BASE/'.runtime/private-media')},
      'shared storage':{'Y3GYM_STATIC_ROOT':str(root/'media')},'relative storage':{'Y3GYM_MEDIA_ROOT':'media'},
      'remote DB without password':{'Y3GYM_DB_HOST':'db.invalid'},
    }
    link=root/'media-link';link.symlink_to(root/'media',target_is_directory=True)
    invalid['symlink media']={'Y3GYM_MEDIA_ROOT':str(link)}
    for label,changes in invalid.items():
        case=dict(env)
        for key,value in changes.items():
            if value is None:case.pop(key,None)
            else:case[key]=value
        p=subprocess.run([sys.executable,'-c',script],cwd=BASE,env=case,capture_output=True)
        if p.returncode==0:raise AssertionError('Unsafe production setting accepted: '+label)
        result['negative_settings'].append(label)
    drill.command([sys.executable,'manage.py','check','--deploy'],'production-check-deploy.log',env)
    drill.command([sys.executable,'manage.py','collectstatic','--noinput'],'production-collectstatic.log',env)
    assert (root/'static/site.css').read_bytes()==(BASE/'assets/site.css').read_bytes()
    result['collectstatic_files']=sum(p.is_file() for p in (root/'static').rglob('*'))
    # Django contract checks include response headers/secure cookies and an actual
    # DB-backed 500 fallback with DEBUG=False; no settings/environment dump.
    drill.command([sys.executable,'-c',
      "import django;django.setup();from scripts.production_probe import django_checks;django_checks()"],
      'production-django-checks.log',env)
    for trust in [False,True]:
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        case={**env,'Y3GYM_BIND':f'127.0.0.1:{port}','Y3GYM_TRUSTED_PROXY_IPS':'127.0.0.1' if trust else ''}
        logfile=drill.root/('gunicorn-trusted.log' if trust else 'gunicorn-untrusted.log')
        with logfile.open('x') as log:
            process=subprocess.Popen([sys.executable,'-m','gunicorn','--config','config/gunicorn.conf.py','config.wsgi:application'],
                                     cwd=BASE,env=case,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            for _ in range(100):
                if process.poll() is not None:raise AssertionError('Gunicorn failed to start; see isolated log')
                try:request(port,'/');break
                except OSError:time.sleep(.1)
            else:raise AssertionError('Gunicorn startup timeout')
            status,headers,body=request(port,'/',forwarded=True)
            assert status==(200 if trust else 301),(trust,status)
            result['http_checks'].append('trusted HTTPS header gives 200' if trust else 'untrusted HTTPS header ignored; 301')
            if trust:
                for path,expected in [('/api/v1/site/',200),('/api/v1/posts/',200),('/admin/',302),('/admin/login/',200),('/cms-files/original_images/TEST-draft.png',403),('/missing/',404),('/static/site.css',404),('/media/original_images/TEST-site.png',404)]:
                    status,headers,body=request(port,path,forwarded=True)
                    assert status==expected,(path,status)
                    assert b'Traceback' not in body
                    result['http_checks'].append(f'{path}: {status}')
                # Exercise actual restored public and draft-only image routes.
                snapshot=json.loads((drill.root/'dst-snapshot.json').read_text())
                from urllib.parse import urlsplit
                image_path=urlsplit(snapshot['post']['cover_image']['url']).path
                assert request(port,image_path,forwarded=True)[0]==200
                result['http_checks'].append('restored public image bytes: 200')
                assert request(port,'/',host='evil.invalid',forwarded=True)[0]==400
                assert request(port,'/admin/login/',forwarded=True,method='POST',body=b'username=TEST&password=invalid')[0]==403
                assert request(port,'/',forwarded=False)[0]==301
                result['http_checks'].extend(['bad Host 400','CSRF missing POST 403','HTTP redirect 301'])
        finally:
            if process.poll() is None:process.send_signal(signal.SIGTERM)
            process.wait(timeout=40)
            assert 'Control socket listening' not in logfile.read_text()
            result.setdefault('stopped_processes',[]).append({'pid':process.pid,'returncode':process.returncode})
    with (drill.root/'production-result.json').open('x') as f:json.dump(result,f,indent=2)
    return result


def django_checks():
    from django.conf import settings
    from django.test import Client, RequestFactory, override_settings
    from django.urls import path
    from django.http import HttpResponse
    from content.views import server_error
    assert not settings.DEBUG and settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
    assert settings.SECURE_PROXY_SSL_HEADER is None and not settings.USE_X_FORWARDED_HOST
    client=Client(enforce_csrf_checks=True,raise_request_exception=False)
    response=client.get('/admin/login/',secure=True,HTTP_HOST='gym.invalid')
    csrf=response.cookies[settings.CSRF_COOKIE_NAME]
    assert csrf['secure'] and csrf['path']=='/' and not csrf['domain']
    def session(request):request.session['synthetic']='TEST';return HttpResponse('TEST')
    def crash(request):raise RuntimeError('TEST INTERNAL PRIVATE DETAIL')
    global urlpatterns,handler500
    urlpatterns=[path('session/',session),path('crash/',crash)];handler500=server_error
    with override_settings(ROOT_URLCONF=__name__):
        response=client.get('/session/',secure=True,HTTP_HOST='gym.invalid')
        cookie=response.cookies[settings.SESSION_COOKIE_NAME]
        assert cookie['secure'] and cookie['httponly'] and not cookie['domain']
        response=client.get('/crash/',secure=True,HTTP_HOST='gym.invalid')
        assert response.status_code==500 and b'TEST INTERNAL PRIVATE DETAIL' not in response.content and b'Traceback' not in response.content
    assert response['X-Content-Type-Options']=='nosniff'
    assert response['X-Frame-Options']=='DENY'
    print('PASS: secure CSRF/session cookie attributes, no arbitrary proxy trust, generic 500, security headers')
