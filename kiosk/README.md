# Raspberry Pi 5 kiosk

This image uses Raspberry Pi OS Desktop (64-bit) dated 2026-10-06, Chromium, labwc, NetworkManager and Tailscale 1.104.7. The board opens at http://127.0.0.1:8080 from storage, including its JSON, fonts and graphics. On first boot, the image provisions itself locally and reboots once. Later boots open the board as soon as the desktop starts. Use a 16 GB or larger microSD card.

## Install

1. In Raspberry Pi Imager, select **Use custom**, select the kiosk image, then choose the target microSD card. Skip OS customization because this image runs its own setup. Flashing erases the selected card.
2. Reinsert the card and open the visible boot partition. Copy `wifi.example.json` to `wifi.json` there and replace the sample values. The first listed network has highest priority. This supports WPA-personal networks with printable ASCII passphrases. The image is set to the US Wi-Fi regulatory region.
3. For remote access, create a short-lived, single-use Tailscale authentication key for this device. Save just that key in `tailscale.key` on the boot partition. Configure tailnet network and SSH rules allowing only your designated administrators to connect to the device as `kioskadmin`. This account has sudo access. For a tagged device, have the auth key apply the tag referenced by your rules.
4. Insert the card in the Pi 5 and connect HDMI and power. Both provisioning files are removed from the boot partition after their respective imports succeed. Keep the card and provisioning files private. Each Pi enrolls independently.
5. After enrollment, connect from a permitted tailnet device with `ssh kioskadmin@<pi-tailscale-name-or-address>`. Find its name or address in the Tailscale admin console. No public SSH listener is needed.
6. If Wi-Fi changes, plug in a keyboard and press **Ctrl+Alt+W**. Enter the network's SSID and follow the masked password prompt. The menu attempts to restore the previously active profile if activation fails. The board continues to run behind the menu.
7. Turn off any auto-off or eco timer configured on the TV itself.

## Content and update recovery

The Pi tracks the `pi-kiosk` branch during this rollout. Commit pricing edits to `menu.json` there. The public website tracks `main` separately. A timer checks the GitHub tree at boot and about every five minutes. It downloads only changed site blobs, checks their hashes, validates the staged menu and referenced files, and switches the site directory atomically. The browser detects the local revision change and reloads. Changes to the OS scripts in this directory are applied by rebuilding the image or maintaining the Pi over SSH.

For diagnostics use `journalctl -u blazin-update -u blazin-wifi -u blazin-enroll`. If a displayed update needs undoing, stop the update timer, wait for any running update service to finish, and point `/var/lib/blazin-kiosk/current` at the directory referenced by `/var/lib/blazin-kiosk/previous`. Leave the timer stopped until the corrected update is on GitHub. Afterwards start `blazin-update.timer` again. The active and previous files are stored locally, so ordinary connection failures require no manual action.

## Rebuild the image

Use Python 3.11+, Git, mtools and xz. Run from the checked-out `pi-kiosk` branch. The builder verifies both pinned archives and modifies a workspace image file only.

```sh
curl -fLO https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2026-10-06/2026-10-06-raspios-trixie-arm64.img.xz
curl -fLO https://pkgs.tailscale.com/stable/tailscale_1.104.7_arm64.tgz
python3 kiosk/build-image.py 2026-10-06-raspios-trixie-arm64.img.xz tailscale_1.104.7_arm64.tgz BlazinKutz-Pi5-Kiosk.img.xz
```

Use the generated SHA-256 file to check the compressed image before flashing. Never add real provisioning files or disk images to Git.
