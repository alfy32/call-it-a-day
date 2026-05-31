#!/usr/bin/env python3
"""D-Bus screen lock listener for Call It a Day.

Subscribes to org.gnome.ScreenSaver.ActiveChanged on the session bus.
- Screen unlock  → POST start (begins a session)
- Screen lock    → POST end   (closes the session)
- SIGTERM        → POST end then exit (clean shutdown on reboot/stop)

On startup, posts a start event so the current login is tracked immediately.
"""

import json
import os
import signal
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime

import dbus
import dbus.mainloop.glib
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib


def _now_iso():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def load_config():
    url = os.environ.get('CALLITADAY_SERVER_URL', '').rstrip('/')
    name = os.environ.get('CALLITADAY_COMPUTER_NAME', '')

    if not url or not name:
        config_path = os.path.expanduser('~/.config/callitaday/config')
        if os.path.exists(config_path):
            with open(config_path) as f:
                for raw in f:
                    raw = raw.strip()
                    if raw.startswith('CALLITADAY_SERVER_URL=') and not url:
                        url = raw.split('=', 1)[1].strip().rstrip('/')
                    elif raw.startswith('CALLITADAY_COMPUTER_NAME=') and not name:
                        name = raw.split('=', 1)[1].strip()

    if not url:
        print('Error: CALLITADAY_SERVER_URL not set. Run install.sh first.', file=sys.stderr)
        sys.exit(1)

    if not name:
        name = socket.gethostname()

    return url, name


def post(server_url, computer_name, action):
    payload = json.dumps({
        'computer': computer_name,
        'action': action,
        'timestamp': _now_iso(),
    }).encode()
    req = urllib.request.Request(
        server_url + '/api/sync',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            return body.get('status', '?')
    except urllib.error.HTTPError as e:
        print(f'HTTP {e.code}: {e.read().decode()}', file=sys.stderr)
    except urllib.error.URLError as e:
        print(f'Connection error: {e.reason}', file=sys.stderr)
    return 'error'


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    server_url, computer_name = load_config()

    try:
        bus = dbus.SessionBus()
    except dbus.DBusException as e:
        print(f'Cannot connect to D-Bus session bus: {e}', file=sys.stderr)
        sys.exit(1)

    loop = GLib.MainLoop()

    def on_active_changed(is_locked):
        if is_locked:
            status = post(server_url, computer_name, 'end')
            print(f'Screen locked   → end posted ({status})', flush=True)
        else:
            status = post(server_url, computer_name, 'start')
            print(f'Screen unlocked → start posted ({status})', flush=True)

    def on_terminate(signum, frame):
        print('Shutting down → posting end', flush=True)
        post(server_url, computer_name, 'end')
        loop.quit()

    bus.add_signal_receiver(
        on_active_changed,
        signal_name='ActiveChanged',
        dbus_interface='org.gnome.ScreenSaver',
        path='/org/gnome/ScreenSaver',
    )

    signal.signal(signal.SIGTERM, on_terminate)
    signal.signal(signal.SIGINT, on_terminate)

    # Post start on launch so a fresh login after a reboot is tracked
    status = post(server_url, computer_name, 'start')
    print(f'Started → start posted ({status})', flush=True)
    print('Listening for screen lock/unlock events…', flush=True)

    loop.run()


if __name__ == '__main__':
    main()
