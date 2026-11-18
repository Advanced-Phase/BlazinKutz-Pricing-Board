#!/usr/bin/env python3
"""Build a flashable Pi image from the pinned Raspberry Pi OS archive."""
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile


OS_SHA = "976766570bee2aaf3047dd78649cfe82abb8fe9687b7f15030cd533ba4e9f7a9"
TAIL_SHA = "d6bed2720310b328b861f943d7b4016c5358a9bad60575eb51e8143b79068484"
TAIL_VERSION = "1.104.7"
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent


def verify(path, expected):
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"Unexpected SHA-256: {path}")


def build(os_archive, tailscale_archive, output):
    verify(os_archive, OS_SHA)
    verify(tailscale_archive, TAIL_SHA)
    with tempfile.TemporaryDirectory(dir=output.parent) as workspace:
        work = Path(workspace)
        image = work / "kiosk.img"
        with lzma.open(os_archive) as source, image.open("wb") as target:
            shutil.copyfileobj(source, target, 8 * 1024 * 1024)
        with image.open("rb") as stream:
            mbr = stream.read(512)
        if mbr[-2:] != b"\x55\xaa" or mbr[450] not in (0x0B, 0x0C, 0x0E):
            raise ValueError("Unexpected Raspberry Pi boot partition")
        sector, _ = struct.unpack_from("<II", mbr, 454)
        fat = f"{image}@@{sector * 512}"
        payload = work / "blazin-kiosk"
        payload.mkdir()
        shutil.copy2(HERE / "firstboot.sh", payload)
        shutil.copytree(HERE, payload / "runtime", ignore=shutil.ignore_patterns(
            "build-image.py", "firstboot.sh", "README.md", "wifi*.json", "tailscale.key", "__pycache__", ".DS_Store"))
        site = payload / "site"
        site.mkdir()
        files = subprocess.check_output(["git", "-C", str(PROJECT), "ls-files", "-z",
                                         "index.html", "app.js", "styles.css", "menu.json", "assets"])
        manifest = {}
        for name in files.decode().strip("\0").split("\0"):
            data = (PROJECT / name).read_bytes()
            destination = site / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            manifest[name] = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        (site / ".manifest").write_text(json.dumps(manifest, sort_keys=True))
        with tarfile.open(tailscale_archive) as archive:
            for name in ("tailscale", "tailscaled"):
                member = archive.extractfile(f"tailscale_{TAIL_VERSION}_arm64/{name}")
                with member, (payload / name).open("wb") as target:
                    shutil.copyfileobj(member, target)
        cmdline = work / "cmdline.txt"
        subprocess.run(["mcopy", "-i", fat, "::cmdline.txt", str(cmdline)], check=True)
        cmdline.write_text(cmdline.read_text().strip() +
                           " consoleblank=0 systemd.run=/boot/firmware/blazin-kiosk/firstboot.sh"
                           " systemd.run_success_action=reboot systemd.unit=kernel-command-line.target\n")
        subprocess.run(["mcopy", "-i", fat, "-o", str(cmdline), "::cmdline.txt"], check=True)
        subprocess.run(["mcopy", "-i", fat, "-s", str(payload), "::/"], check=True)
        subprocess.run(["mcopy", "-i", fat, str(HERE / "wifi.example.json"), "::wifi.example.json"], check=True)
        subprocess.run(["mdir", "-i", fat, "::blazin-kiosk"], check=True)
        compressed = work / "kiosk.img.xz"
        with compressed.open("wb") as target:
            subprocess.run(["xz", "-T2", "-3", "-c", str(image)], stdout=target, check=True)
        compressed.replace(output)
    with output.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    output.with_name(output.name + ".sha256").write_text(f"{digest}  {output.name}\n")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: build-image.py BASE.img.xz TAILSCALE.tgz OUTPUT.img.xz")
    build(*(Path(argument).resolve() for argument in sys.argv[1:]))
