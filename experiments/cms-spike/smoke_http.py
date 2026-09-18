"""Loopback HTTP smoke; starts and stops only its own development server."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

base = Path(__file__).resolve().parent
runtime = base / ".runtime"
demo = json.loads((runtime / "demo.json").read_text())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spike.settings")
import django
django.setup()
from bs4 import BeautifulSoup
from wagtail.images import get_image_model
draft_asset = get_image_model().objects.get(pk=demo["images"]["SPIKE TEST draft-body.png"])
with socket.socket() as probe:
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
origin = f"http://127.0.0.1:{port}"
results = []


def get(path, expected, image=False):
    try:
        response = urllib.request.urlopen(origin + path, timeout=3)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        data = response.read()
        status = response.status
        cache = response.headers.get("Cache-Control", "")
        content_type = response.headers.get("Content-Type", "")
    assert status == expected, (path, status, expected)
    if not path.startswith("/static/"):
        assert "no-store" in cache, path
    if image:
        assert content_type.startswith("image/") and data.startswith(b"\x89PNG"), path
    if expected >= 400:
        assert not content_type.startswith("image/"), path
    results.append({"path": path, "status": status, "cache_control": cache, "content_type": content_type})
    return data


with (runtime / "http-server.log").open("a") as log:
    process = subprocess.Popen([sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload", "--insecure"], cwd=base, stdout=log, stderr=log)
    try:
        for attempt in range(40):
            if process.poll() is not None:
                raise RuntimeError("Own development server exited before readiness; inspect http-server.log")
            try:
                with urllib.request.urlopen(origin + "/admin/login/", timeout=1):
                    break
            except (OSError, urllib.error.URLError):
                time.sleep(0.25)
        else:
            raise RuntimeError("Own development server did not become ready")
        get("/admin/login/", 200)
        get("/static/wagtailadmin/css/core.css", 200)
        pk = demo["posts"]["a"]
        html = get(f"/spike/posts/{pk}/", 200)
        data = json.loads(get(f"/spike/posts/{pk}/json/", 200))["data"]
        assert data["title"] == "SPIKE PUBLIC A" and b"SPIKE DRAFT A" not in html
        get(urllib.parse.urlsplit(data["cover_image"]["url"]).path, 200, image=True)
        for image in BeautifulSoup(data["body_html"], "html.parser").find_all("img"):
            get(urllib.parse.urlsplit(image["src"]).path, 200, image=True)
        draft_image = demo["images"]["SPIKE TEST draft-body.png"]
        get(f"/spike/display/{draft_image}/", 404)
        get(draft_asset.file.url, 403)
        get("/media/" + draft_asset.file.name, 404)
        get("/.runtime/secret-key", 404)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        record = {"pid": process.pid, "loopback": origin, "stopped": process.poll() is not None, "requests": results}
        # Each execution keeps its own evidence; no resetting prior DB/media/logs.
        evidence = runtime / f"http-smoke-{time.time_ns()}.json"
        evidence.write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
