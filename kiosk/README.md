# Raspberry Pi 5 kiosk

This image uses Raspberry Pi OS Desktop (64-bit) dated 2026-10-06, Chromium, labwc, NetworkManager and Tailscale 1.104.7. The board opens at http://127.0.0.1:8080 from storage, including its JSON, fonts and graphics. On first boot, the image provisions itself locally and reboots once. Later boots open the board as soon as the desktop starts. Use a 16 GB or larger microSD card.

## 1. Flash the microSD card

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on your Mac, Windows PC, or Linux computer. A 16 GB or larger card is recommended. Flashing erases the selected card.

1. Put `BlazinKutz-Pi5-Kiosk.img.xz` and its `.sha256` companion in the same folder. On macOS, open Terminal in that folder and run `shasum -a 256 -c BlazinKutz-Pi5-Kiosk.img.xz.sha256`. Proceed when it reports `OK`.
2. Choose **Raspberry Pi 5** as the device. Under OS, choose **Use custom** and select the `.img.xz` file.
3. Select the microSD card by its capacity and name. If asked, choose **Skip customisation**. The kiosk image contains its own first-boot setup.
4. Wait for writing and verification to finish. Reinsert the card to mount **bootfs**. If macOS offers to initialize an unreadable partition, choose **Ignore**. The Linux partition is for the Pi.
5. Add the provisioning files described below to the top level of **bootfs**. Eject the card before moving it to the Pi.

[balenaEtcher](https://etcher.balena.io/) is also an option. If it does not accept the compressed file, decompress it with `xz -dk BlazinKutz-Pi5-Kiosk.img.xz` and select the resulting `.img` in Etcher. Use **Flash from file**, choose the microSD card, and wait for verification.

## 2. Preconfigure Wi-Fi and remote access

Place these files next to `cmdline.txt` on **bootfs**, which the Pi mounts as `/boot/firmware`. Use plain text and the exact filenames. In Finder, check that TextEdit did not append `.txt`.

| File | When to include it | Contents |
| --- | --- | --- |
| `wifi.json` | For automatic Wi-Fi setup | SSIDs and passwords in the JSON format below. Skip it if the Pi will use Ethernet or you will set Wi-Fi with the keyboard menu. |
| `tailscale.key` | For Tailscale remote access | A single Tailscale auth key on its own line. Skip it for a local-only display. |

Both files are optional for booting the local board. The image already contains the OS, browser, board, and Tailscale software.

### Wi-Fi file

Copy the supplied [wifi.example.json](wifi.example.json) to `wifi.json` on **bootfs** and replace the placeholders. Put the preferred network first. A single entry is enough.

```json
{
  "networks": [
    { "ssid": "Shop Wi-Fi", "password": "ReplaceWithShopPassword" },
    { "ssid": "Backup Wi-Fi", "password": "ReplaceWithBackupPassword" }
  ]
}
```

The importer supports WPA-personal networks with printable ASCII passphrases of 8–63 characters. Use JSON escapes for quotation marks and backslashes. The image is set to the US Wi-Fi regulatory region. The provisioning file is removed after the profiles import successfully. A successful import means the profiles were saved, so test the actual Wi-Fi connection separately.

### Tailscale key and SSH credentials

1. In [Tailscale Admin → Keys](https://login.tailscale.com/admin/settings/keys), generate a short-lived, single-use **auth key** for this Pi. If your access rules use a device tag, apply that tag to the key. Use a separate key for each Pi.
2. Save the key as `tailscale.key` on **bootfs**. The file contains only the generated key, with no quotes or JSON. The Pi retries enrollment when internet is available and removes the file after enrollment succeeds.
3. In [Tailscale Access Controls](https://login.tailscale.com/admin/acls), allow the designated admin account to reach this Pi on TCP 22 and add a Tailscale SSH rule allowing that account to sign in as `kioskadmin`. Both permissions are required. See the [Tailscale SSH setup guide](https://tailscale.com/docs/features/tailscale-ssh).
4. Find the Pi in [Tailscale Admin → Machines](https://login.tailscale.com/admin/machines). From a device already signed in to your tailnet, use its Tailscale hostname or address:

   ```sh
   ssh kioskadmin@<pi-tailscale-name-or-ip>
   ```

Your Tailscale identity authorizes SSH. There is no root password, SSH password, or separate SSH key to prepare. `kioskadmin` can use `sudo` for maintenance. Keep provisioning files private and out of Git.

## 3. First boot and recovery

1. Insert the card in the Pi 5 and connect HDMI and power. Let the initial provisioning and automatic reboot finish. The board runs from the Pi even if Wi-Fi or Tailscale is unavailable.
2. Turn off any auto-off or eco timer on the TV itself. The Pi kiosk is configured to stay awake.
3. If Wi-Fi changes, plug in a keyboard and press **Ctrl+Alt+W**. Enter the network SSID and follow the masked password prompt. The board runs behind the menu. If activation fails, the menu attempts to restore the previously active connection.
4. If you skipped Tailscale or its key expires before use, shut down the Pi, put a fresh `tailscale.key` on **bootfs**, and boot again. No reflash is needed.

After SSH is working, check Wi-Fi, Tailscale, and the local display service with:

```sh
nmcli device status
tailscale status
systemctl status blazin-board.service blazin-update.timer
sudo journalctl -b -u blazin-wifi -u blazin-enroll -u blazin-tailscale
```

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
