"""Unapplied Linux candidate. Bind and trusted proxy peers must be explicit."""
import ipaddress
import os
import re
bind = os.environ.get('Y3GYM_BIND', '')
if not re.fullmatch(r'127\.0\.0\.1:[1-9][0-9]{3,4}', bind) or not 1024 <= int(bind.rsplit(':',1)[1]) <= 65535:
    raise RuntimeError('Gunicorn candidate requires an explicit loopback port')
workers = 2
worker_class = 'sync'
timeout = 30
graceful_timeout = 30
umask = 0o077
accesslog = None
errorlog = '-'
# No default localhost trust: only operator-selected exact proxy peers.
forwarded_allow_ips = os.environ.get('Y3GYM_TRUSTED_PROXY_IPS', '')
for address in forwarded_allow_ips.split(',') if forwarded_allow_ips else []:
    ipaddress.ip_address(address)
secure_scheme_headers = {'X-FORWARDED-PROTO': 'https'}
forwarder_headers = ''
proxy_protocol = False

# 26.x enables a control socket by default; this candidate needs no control service.
control_socket_disable = True
