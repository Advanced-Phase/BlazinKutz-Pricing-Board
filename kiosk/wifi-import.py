"""Import per-device Wi-Fi profiles without putting passwords into command arguments."""
import json
import os
from pathlib import Path
import subprocess
import uuid

source = Path("/boot/firmware/wifi.json")
if not source.exists():
    raise SystemExit(0)
os.umask(0o077)
config = json.loads(source.read_text())
profiles = config["networks"]
if not isinstance(profiles, list) or not profiles:
    raise ValueError("Expected a nonempty networks array")
files = []
for index, profile in enumerate(profiles):
    ssid, password = profile["ssid"].encode(), profile["password"]
    if not 1 <= len(ssid) <= 32 or not (8 <= len(password) <= 63 and password.isascii()
                                         and all(32 <= ord(c) <= 126 for c in password)):
        raise ValueError("Invalid WPA personal profile")
    identifier = uuid.uuid5(uuid.NAMESPACE_OID, ssid.hex())
    encoded = ";".join(str(byte) for byte in ssid) + ";"
    psk = password.replace("\\", "\\\\").replace(" ", "\\s")
    body = f"""[connection]
id=Board Wi-Fi {index + 1}
uuid={identifier}
type=wifi
autoconnect-priority={100 - index}
[wifi]
mode=infrastructure
ssid={encoded}
[wifi-security]
key-mgmt=wpa-psk
psk={psk}
[ipv4]
method=auto
[ipv6]
method=auto
"""
    files.append((identifier, body))
for identifier, body in files:
    target = Path(f"/etc/NetworkManager/system-connections/blazin-{identifier}.nmconnection")
    staged = target.with_suffix(".tmp")
    staged.write_text(body)
    staged.replace(target)
subprocess.run(["nmcli", "connection", "reload"], check=True)
source.unlink()
