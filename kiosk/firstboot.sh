#!/bin/bash
set -euo pipefail
boot=/boot/firmware
payload=$boot/blazin-kiosk
root=/var/lib/blazin-kiosk
install -d /opt/blazin-kiosk "$root"
cp -a "$payload/runtime/." /opt/blazin-kiosk/
install -m 755 "$payload/tailscale" "$payload/tailscaled" /usr/local/sbin/
if ! id board >/dev/null 2>&1; then
  useradd -m -s /bin/bash board
  python3 -c 'import secrets; print("board:" + secrets.token_hex(32))' | chpasswd
fi
if ! id kioskadmin >/dev/null 2>&1; then
  useradd -m -s /bin/bash -G sudo kioskadmin
  python3 -c 'import secrets; print("kioskadmin:" + secrets.token_hex(32))' | chpasswd
fi
# Remote privilege is gated by Tailscale SSH policy for this account.
printf 'kioskadmin ALL=(ALL:ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/90-blazin-kiosk
chmod 440 /etc/sudoers.d/90-blazin-kiosk
install -d /etc/lightdm/lightdm.conf.d /home/board/.config/labwc
# Raspberry Pi OS sets wizard autologin in the main LightDM file.
sed -i -e 's/^autologin-user=.*/autologin-user=board/' \
       -e 's/^autologin-session=.*/autologin-session=labwc/' /etc/lightdm/lightdm.conf
test -f /usr/share/wayland-sessions/labwc.desktop
test -f /etc/xdg/labwc/rc.xml
python3 /opt/blazin-kiosk/labwc.py
install -m 755 /opt/blazin-kiosk/autostart /home/board/.config/labwc/autostart
chown -R board:board /home/board/.config
install -d -o board -g board /var/lib/blazin-kiosk/chromium
install -d /etc/chromium/policies/managed
cat >/etc/chromium/policies/managed/blazin-kiosk.json <<'EOF'
{"URLBlocklist":["*"],"URLAllowlist":["http://127.0.0.1:8080"],"DefaultBrowserSettingEnabled":false}
EOF
if [ ! -L "$root/current" ]; then
  cp -a "$payload/site" "$root/site-seed"
  ln -s site-seed "$root/current"
fi
install -m 644 /opt/blazin-kiosk/*.service /opt/blazin-kiosk/*.timer /etc/systemd/system/
raspi-config nonint do_wifi_country US
printf 'blazin-board-%s\n' "$(cut -c1-8 /etc/machine-id)" >/etc/hostname
systemctl enable blazin-enroll.timer blazin-board.service blazin-update.timer blazin-wifi.service blazin-tailscale.service lightdm.service
systemctl set-default graphical.target
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
sed -i 's/ systemd.run=\/boot\/firmware\/blazin-kiosk\/firstboot.sh systemd.run_success_action=reboot systemd.unit=kernel-command-line.target//' "$boot/cmdline.txt"
sync
