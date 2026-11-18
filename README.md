# BlazinKutz Pricing Board

A public, version-controlled home for the Blazin Kutz service menu, maintained by Advanced Phase. The board uses a black, white, and metallic-gold design with the supplied gold-foil logo, animated gold flames and embers, and seamless shimmer effects.

## Files

- `index.html` — board layout and booking link.
- `styles.css` — desktop/mobile sizing, gold theme, and seamless CSS animations.
- `menu.json` — service names, prices, the Early Bird special, and board copy.
- `app.js` — menu rendering, mobile fitting, and animated flames.
- `assets/blazin-kutz-gold-foil.png` — current transparent logo.
- `assets/booking-qr.png` — booking QR code.

No build step or application dependencies are required. Google Fonts are loaded online, with local font fallbacks.

## Preview locally

```sh
python3 -m http.server 8080
```

Open <http://localhost:8080>. For a Raspberry Pi display, use Chromium fullscreen/kiosk mode. The desktop board is designed for a 1920 × 1080 display. Mobile screens up to 1024px wide fit the complete board in either orientation.

## Change pricing

1. Edit `menu.json`. Use `services` for the numbered rows, `earlyBird` for the centered special, and `copy` for headings and notes.
2. Keep `price` numeric. The board adds the dollar sign. Optional `prefix` and `suffix` fields support displays like `+$15` and `$55+`.
3. Preview through the local server above. The browser loads the JSON over HTTP.
4. Commit and push to your working branch. GitHub Pages publishes from `main`.

GitHub's commit history records each update. Use a pull request when a change needs review.

## Download and deploy

Download the current files from [Code → Download ZIP](https://github.com/Advanced-Phase/BlazinKutz-Pricing-Board/archive/refs/heads/main.zip), or clone the repository:

```sh
git clone https://github.com/Advanced-Phase/BlazinKutz-Pricing-Board.git
```

Extract the archive and upload `index.html`, `styles.css`, `app.js`, `menu.json`, and the `assets` directory together to the website directory, replacing the previous versions. Upload the contents of the repository folder rather than nesting that folder inside the website directory.

Pushing to GitHub tracks and distributes the source files; it does not automatically deploy changes to the existing web host. A tagged release can identify a specific pricing version for distribution.

## Animation and mobile behavior

The gold shimmer and drifting embers ease back and forth with matching loop endpoints. Reduced-motion preferences are respected. Mobile renders the composition using scaled CSS lengths and pauses animation briefly while viewport changes settle. Its flame canvas uses a fixed 960 × 103 backing store to avoid reallocating the canvas during rotation.

Local Chrome/WebKit checks cover desktop/mobile fit, seamless CSS loop boundaries, and animation resuming after rotation. Physical iPhone Safari verification remains a separate check.
