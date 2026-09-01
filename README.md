# Shared Household Chores

A Django app for tracking household chores, run for personal use on a home
LAN (local network only — see the warning below).

## Setup

```
uv sync
```

## Run on the LAN

This app has no authentication, so it is only ever meant to be reachable by
devices on your own home network (per `_docs/plan.md`: "no auth, since only
trusted household devices can reach it"). Follow these steps to run it so
other devices on the same LAN — e.g. a phone — can open it in a browser.

### 1. Find your machine's LAN IP address

The exact command depends on your OS:

- **Linux**: `ip addr` (look for the `inet` address on your Wi-Fi/Ethernet
  interface, e.g. `192.168.1.42`)
- **macOS**: `ifconfig` (same idea, look under `en0` or similar)
- **Windows**: `ipconfig` (look for "IPv4 Address" under your active
  network adapter)

This address is different on every machine and network, so there is no
single value to copy — you have to look it up each time you're on a new
network.

### 2. Start the dev server bound to all interfaces

By default, `manage.py runserver` only listens on `localhost`, which other
devices can't reach. Bind it to `0.0.0.0` instead:

```
uv run python manage.py runserver 0.0.0.0:8000
```

### 3. Open the app from another device

On a phone or other device connected to the **same** LAN, open a browser
and go to:

```
http://<machine-lan-ip>:8000
```

replacing `<machine-lan-ip>` with the address you found in step 1, e.g.
`http://192.168.1.42:8000`.

### `ALLOWED_HOSTS`

`config/settings.py` sets `ALLOWED_HOSTS = ["*"]`. Django rejects requests
whose `Host` header isn't in this list with a `DisallowedHost` error, and
since the LAN IP varies per machine/network there's no single fixed value
to allow-list. `["*"]` is acceptable here specifically because the app is
never exposed beyond the LAN — see the warning below — so there's no
untrusted `Host` header to worry about.

> [!WARNING]
> **Never expose this app beyond your home LAN.** It has no
> authentication — anyone who can reach it can see and change everything.
> Do not:
> - forward port 8000 (or any port) on your router to this machine
> - use a tunnel or VPN service (ngrok, Cloudflare Tunnel, Tailscale
>   funnel, etc.) to make it reachable from outside your LAN
> - deploy it to any cloud host or public server
>
> This setup relies entirely on your home network's boundary (i.e. nothing
> outside your LAN can reach it) plus this warning — there is no
> code-level restriction preventing the app from being reached if you do
> expose it.

### Dev-only setup

This is a development configuration, not a production deployment:

- `DEBUG = True` stays on (verbose error pages, auto-reload, etc.)
- It runs on Django's built-in dev server (`manage.py runserver`), not a
  production WSGI server
- It's intended for one household's personal, trusted-device use — not for
  serving the public internet

### Troubleshooting

If a phone or other device can't connect even though it's on the same
LAN, check that your machine's firewall allows incoming connections on
port 8000 (e.g. `ufw` on Linux, Windows Firewall's prompt when the dev
server first starts). Firewall configuration is OS-specific and not
covered here beyond this pointer.

## Commands

- `uv sync` - install dependencies
- `uv run python manage.py test` - the whole test suite
- `uv run python manage.py test chores` - one app's tests
- `uv run python manage.py runserver 0.0.0.0:8000` - run the dev server, reachable from the LAN
