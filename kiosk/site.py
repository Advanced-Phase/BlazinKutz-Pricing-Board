#!/usr/bin/env python3
"""Serve the local board and install verified, incremental content updates."""
import base64
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

FONTS = Path(__file__).resolve().parent / "fonts"
ROOT = Path(os.environ.get("KIOSK_ROOT", "/var/lib/blazin-kiosk")).resolve()
REPO = "Advanced-Phase/BlazinKutz-Pricing-Board"
BRANCH = "pi-kiosk"
REQUIRED = {"index.html", "app.js", "styles.css", "menu.json"}


def site_path(name):
    path = PurePosixPath(name)
    return (name in REQUIRED or (len(path.parts) > 1 and path.parts[0] == "assets"
            and not path.is_absolute() and ".." not in path.parts))


def blob_hash(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def get(url, limit):
    with urlopen(Request(url, headers={"User-Agent": "BlazinKutz-Pi-Kiosk"}), timeout=15) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Download exceeds size limit")
    return data


def validate(directory):
    if not all((directory / name).is_file() for name in REQUIRED):
        raise ValueError("Site is incomplete")
    from urllib.parse import urlsplit
    html = (directory / "index.html").read_text()
    if "</body>" not in html or "menu-columns" not in html:
        raise ValueError("Missing pricing board markup")
    for url in re.findall(r'(?:src|href)="([^"]+)"', html):
        parts = urlsplit(url)
        if site_path(parts.path.lstrip("/")) and not parts.netloc and not parts.scheme:
            if not (directory / parts.path.lstrip("/")).is_file():
                raise ValueError(f"Referenced asset missing: {url}")
    menu = json.loads((directory / "menu.json").read_text())
    if not isinstance(menu["copy"], dict) or not isinstance(menu["services"], list) or not menu["services"]:
        raise ValueError("Invalid menu structure")
    for item in [*menu["services"], menu["earlyBird"]]:
        if not (isinstance(item["name"], str) and item["name"].strip()
                and isinstance(item["detail"], str)
                and type(item["price"]) in (float, int) and 0 <= item["price"] < 100000):
            raise ValueError("Invalid service")
    if not all(isinstance(value, str) for value in menu["copy"].values()):
        raise ValueError("Invalid board copy")


def activate(target, name):
    temporary = ROOT / (name + ".next")
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(target, target_is_directory=True)
    temporary.replace(ROOT / name)


def update():
    current = (ROOT / "current").resolve(strict=True)
    old = json.loads((current / ".manifest").read_text())
    tree = json.loads(get(f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1", 2_000_000))
    if tree["truncated"]:
        raise ValueError("Incomplete GitHub tree")
    new = {item["path"]: item["sha"] for item in tree["tree"]
           if item["mode"] == "100644" and site_path(item["path"])}
    if old == new:
        return
    if not REQUIRED <= new.keys():
        raise ValueError("Required board files missing from GitHub")
    with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
        staged = Path(temporary) / "site"
        staged.mkdir()
        for name, sha in new.items():
            destination = staged / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            local = current / name
            if old.get(name) == sha and local.is_file() and blob_hash(local.read_bytes()) == sha:
                os.link(local, destination)
            else:
                # The blob API addresses the precise bytes by object ID.
                blob = json.loads(get(f"https://api.github.com/repos/{REPO}/git/blobs/{sha}", 16_000_000))
                data = base64.b64decode(blob["content"])
                if blob_hash(data) != sha:
                    raise ValueError(f"Blob verification failed: {name}")
                destination.write_bytes(data)
        validate(staged)
        (staged / ".manifest").write_text(json.dumps(new, sort_keys=True))
        target = ROOT / ("site-" + tree["sha"])
        if not target.exists():
            staged.rename(target)
        activate(current, "previous")
        activate(target, "current")
        for directory in ROOT.glob("site-*"):
            if directory not in (target, current):
                shutil.rmtree(directory)
        print(f"Activated {target.name}", flush=True)


class BoardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "current"), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'")
        super().end_headers()

    def do_GET(self):
        from urllib.parse import urlsplit
        path = urlsplit(self.path).path
        if path.startswith("/kiosk-fonts/"):
            font = FONTS / path.removeprefix("/kiosk-fonts/")
            if font.parent == FONTS and font.is_file() and font.suffix in (".woff2", ".css"):
                return self.send_bytes(font.read_bytes(), "font/woff2" if font.suffix == ".woff2" else "text/css")
            self.send_error(404)
            return
        if path == "/revision":
            return self.send_bytes((ROOT / "current").resolve().name.encode(), "text/plain")
        if path == "/kiosk-refresh.js":
            return self.send_bytes(b"""
let displayed = new URL(document.currentScript.src).searchParams.get("revision");
async function check() {
  try {
    const revision = await (await fetch('/revision')).text();
    if (displayed && displayed !== revision) location.reload();
    displayed = revision;
  } catch {}
}
check();
setInterval(check, 5000);
""", "text/javascript")
        if path in ("/", "/index.html"):
            current = (ROOT / "current").resolve()
            html = (current / "index.html").read_text()
            html = re.sub(r'<link[^>]+fonts\.google(?:apis|static)\.com[^>]*>', '', html)
            html = html.replace("</head>", '<link rel="stylesheet" href="/kiosk-fonts/fonts.css"></head>')
            return self.send_bytes(html.replace("</body>", f'<script src="/kiosk-refresh.js?revision={current.name}"></script></body>').encode(), "text/html; charset=utf-8")
        if not site_path(path.lstrip("/")):
            self.send_error(404)
            return
        super().do_GET()

    def send_bytes(self, data, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    if sys.argv[1:] == ["update"]:
        update()
    else:
        ThreadingHTTPServer(("127.0.0.1", 8080), BoardHandler).serve_forever()
