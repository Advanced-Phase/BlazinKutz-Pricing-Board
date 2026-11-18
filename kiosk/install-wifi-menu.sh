#!/bin/bash
set -euo pipefail
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
install -d /opt/blazin-kiosk /etc/polkit-1/rules.d
install -m 755 "$source_dir/wifi-menu" "$source_dir/wifi-menu-ui" /opt/blazin-kiosk/
install -m 644 "$source_dir/49-blazin-wifi.rules" /etc/polkit-1/rules.d/
