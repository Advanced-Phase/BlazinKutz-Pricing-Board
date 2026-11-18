# Raspberry Pi 5 kiosk

This image uses Raspberry Pi OS Desktop (64-bit) dated 2026-10-06, Chromium, labwc, NetworkManager and Tailscale 1.104.7. The board opens at http://127.0.0.1:8080 from storage, including its JSON, fonts and graphics. On first boot, the image provisions itself locally and reboots once. Later boots open the board as soon as the desktop starts. Use a 16 GB or larger microSD card.

## 1. Flash the microSD card

Both programs can flash this prebuilt kiosk image. Use whichever you already have. Start with a 16 GB or larger microSD card. Flashing erases the selected card, so double-check the destination by name and capacity.

Put `BlazinKutz-Pi5-Kiosk-WayVNC.img` and its `.sha256` companion in the same folder. On macOS, open Terminal in that folder and verify the download:

```sh
shasum -a 256 -c BlazinKutz-Pi5-Kiosk-WayVNC.img.sha256
```

Proceed when it reports `OK`.

### Option A: balenaEtcher

1. Open [balenaEtcher](https://etcher.balena.io/) and insert the microSD card.
2. Click **Flash from file** and select `BlazinKutz-Pi5-Kiosk-WayVNC.img`.
3. Click **Select target** and choose the microSD card.
4. Click **Flash!** and approve the operating system prompt if shown. Wait for writing and validation to finish.

### Option B: Raspberry Pi Imager

1. Open [Raspberry Pi Imager](https://www.raspberrypi.com/software/) and insert the microSD card.
2. Select **Raspberry Pi 5** as the device. Under OS, choose **Use custom** and select `BlazinKutz-Pi5-Kiosk-WayVNC.img`.
3. Under Storage, select the microSD card. If prompted, choose **Skip customisation**. This image already includes its first-boot setup.
4. Confirm the write and wait for verification to finish.

The same flashing steps apply to older or custom `.img.xz` builds. If Etcher has trouble with a compressed image, run `xz -dk YOUR_IMAGE.img.xz` and select the resulting `.img`.

### After flashing with either tool

1. Reinsert the card and open **bootfs**. If macOS offers to initialize an unreadable partition, choose **Ignore**. The unreadable Linux partition is expected.
2. Add any provisioning files you want to use to the top level of **bootfs**, next to `cmdline.txt`, as described below.
3. Eject the card, insert it into the Pi, and power on.

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
3. If Wi-Fi changes, plug in a keyboard and press **Ctrl+Alt+W**. The board runs behind the menu. Choose **View saved Wi-Fi profiles and passwords** to see the active connection name and saved Wi-Fi settings. Passwords are visible on the TV while that option is open. Press Enter to hide them. Choose **Edit or add a Wi-Fi profile**, then select an existing profile or choose **Add → Wi-Fi**. Enter the SSID and security settings, set the password, and save. Choose **Activate a saved network** to connect. If the new profile fails, select your previous network.
4. Press **Escape** from any Wi-Fi menu screen to close the window and discard edits still in the open form. Changes already saved or activation already submitted are kept. To save first, choose **OK** inside the editor before pressing Escape.
5. If you skipped Tailscale or its key expires before use, shut down the Pi, put a fresh `tailscale.key` on **bootfs**, and boot again. No reflash is needed.

After SSH is working, check Wi-Fi, Tailscale, and the local display service with:

```sh
nmcli device status
tailscale status
systemctl status blazin-board.service blazin-update.timer
sudo journalctl -b -u blazin-wifi -u blazin-enroll -u blazin-tailscale
```

### Update the menu on an already flashed Pi

From the project directory on your computer, copy the four Wi-Fi menu files over Tailscale SSH. Substitute your Pi’s Tailscale hostname for `PI_NAME`.

```sh
scp kiosk/{wifi-menu,wifi-menu-ui,49-blazin-wifi.rules,install-wifi-menu.sh} kioskadmin@PI_NAME:
ssh kioskadmin@PI_NAME 'sudo bash ~/install-wifi-menu.sh'
```

Close any open Wi-Fi menu and press **Ctrl+Alt+W** again. This installs the menu and a NetworkManager permission rule scoped to the active local kiosk account. The rule allows that account to manage NetworkManager profiles, so use the editor on the dedicated kiosk.

## View the HDMI output remotely with WayVNC

The image starts WayVNC in the same Labwc session as Chromium, so it mirrors the connected output, including animations and local dialogs. Use one HDMI display for the kiosk. WayVNC disables remote keyboard and mouse input and automatic display resizing. Capture is limited to 15 fps to reduce bandwidth. The local display keeps its normal animation speed.

WayVNC listens only on the Pi’s loopback address `127.0.0.1:5900`. Use the existing Tailscale SSH connection to tunnel to that port. The shop LAN and public internet have no VNC listener. There is no separate VNC password because the tunnel requires an authorized Tailscale SSH login. Keep the SSH policy scoped to your administrators. The password screen in the Wi-Fi menu is visible to an authorized viewer if someone opens it locally.

1. Boot the Pi with HDMI connected. Enroll it with `tailscale.key` using the instructions above. From your viewing computer, sign into the same tailnet and verify that `ssh kioskadmin@PI_NAME` works.
2. On the viewing computer, start the tunnel. Replace `PI_NAME` with the Pi’s Tailscale hostname or IP address. Leave this terminal open.

   ```sh
   ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:5901:127.0.0.1:5900 kioskadmin@PI_NAME
   ```

3. Open a VNC viewer on that same computer. On a Mac, try Finder → **Go → Connect to Server** and enter `vnc://127.0.0.1:5901`. With TigerVNC Viewer, enter `127.0.0.1::5901` (the double colon selects a TCP port). If a viewer rejects the local no-password connection, use TigerVNC.
4. Close the viewer and press **Ctrl+C** in the tunnel terminal when finished.

If the tunnel opens but the viewer shows no screen, verify that the kiosk session is logged in and HDMI is connected. From SSH, run:

```sh
ss -ltn 'sport = :5900'
sudo tail -n 30 /home/board/.blazin-wayvnc.log
```

The listener should appear as `127.0.0.1:5900`. WayVNC needs a running graphical session and a detected output. Its picture confirms what the Pi renders and cannot verify which input the TV is actually showing. See [WayVNC](https://manpages.debian.org/trixie/wayvnc/wayvnc.1.en.html) and [Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh).

### Add WayVNC to an already flashed kiosk

Copy the updated files from the project directory to an enrolled Pi. Restarting LightDM in the last step briefly interrupts the displayed board.

```sh
scp kiosk/{autostart,wayvnc.conf} kioskadmin@PI_NAME:
ssh kioskadmin@PI_NAME 'sudo install -m 644 ~/wayvnc.conf /opt/blazin-kiosk/wayvnc.conf && sudo install -m 755 ~/autostart /opt/blazin-kiosk/autostart && sudo install -o board -g board -m 755 ~/autostart /home/board/.config/labwc/autostart && sudo systemctl restart lightdm'
```

## Content and update recovery

The Pi tracks the `pi-kiosk` branch during this rollout. Commit pricing edits to `menu.json` there. The public website tracks `main` separately. A timer checks the GitHub tree at boot and about every five minutes. It downloads only changed site blobs, checks their hashes, validates the staged menu and referenced files, and switches the site directory atomically. The browser detects the local revision change and reloads. Changes to the OS scripts in this directory are applied by rebuilding the image or maintaining the Pi over SSH.

For diagnostics use `journalctl -u blazin-update -u blazin-wifi -u blazin-enroll`. If a displayed update needs undoing, stop the update timer, wait for any running update service to finish, and point `/var/lib/blazin-kiosk/current` at the directory referenced by `/var/lib/blazin-kiosk/previous`. Leave the timer stopped until the corrected update is on GitHub. Afterwards start `blazin-update.timer` again. The active and previous files are stored locally, so ordinary connection failures require no manual action.

## Rebuild the image

Use Python 3.11+, Git and mtools. Install xz if you want a compressed output. Run from the checked-out `pi-kiosk` branch. The builder verifies both pinned archives and modifies a workspace image file only.

```sh
curl -fLO https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2026-10-06/2026-10-06-raspios-trixie-arm64.img.xz
curl -fLO https://pkgs.tailscale.com/stable/tailscale_1.104.7_arm64.tgz
python3 kiosk/build-image.py 2026-10-06-raspios-trixie-arm64.img.xz tailscale_1.104.7_arm64.tgz BlazinKutz-Pi5-Kiosk-WayVNC.img
```

Use the generated SHA-256 file to check the image before flashing. Use an output name ending in `.img.xz` for a compressed build. Never add real provisioning files or disk images to Git.
