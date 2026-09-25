# -*- coding: utf-8 -*-
"""
Stablecoin Payment Gateway — Entry Point
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _ensure_console():
    """Attach a real console when the process was launched without one —
    from IDLE (``pythonw``) or via a no-console interpreter association.
    The terminal UI needs genuine console handles: rich reads
    ``sys.__stdin__``/``sys.__stdout__`` (the *original* streams, which are
    ``None`` under ``pythonw``). IDLE only substitutes pseudo-files for
    ``sys.std*``, so the check must be the console window itself, never the
    std streams. The reopened streams are assigned to BOTH ``sys.std*`` and
    ``sys.__std*__``."""
    if os.name != "nt":
        return
    try:
        import ctypes
        if ctypes.windll.kernel32.GetConsoleWindow():
            return
        if not ctypes.windll.kernel32.AllocConsole():
            return
        ctypes.windll.kernel32.SetConsoleCP(65001)
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        _in = open("CONIN$", "r", encoding="utf-8", errors="replace")
        _out = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        _err = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        sys.__stdin__ = sys.stdin = _in
        sys.__stdout__ = sys.stdout = _out
        sys.__stderr__ = sys.stderr = _err
    except Exception:
        pass


_ensure_console()


def _utf8_stdio():
    """Reconfigure std streams as UTF-8 with replacement fallback.
    run.bat sets codepage 65001 before launch, but a bare ``python main.py``
    on a cp1252/cp866 machine (or with output piped to a file) would
    otherwise crash rich on the first emoji with UnicodeEncodeError.
    ``errors="replace"`` degrades glyphs instead of crashing."""
    for stream_name in ("stdin", "stdout", "stderr",
                        "__stdin__", "__stdout__", "__stderr__"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


_utf8_stdio()

# Immediate lifeline for the user before ANY heavy work (runtime provisioning,
# re-exec, rich imports): without this line a cold start shows a bare black
# window for seconds-to-a-minute and reads as "hung". Plain ASCII, flushed —
# must survive every console state.
print("  Loading, please wait...", flush=True)

# Re-exec under the bundled runtime FIRST on 64-bit Windows whenever it can
# be provisioned: dependency installation must target the interpreter that
# will actually run the app. The bundled image ships with every dependency
# pre-installed, so the re-exec'd start needs no pip and no network at all;
# the bootstrap interpreter below is only a trampoline (its version, pip
# state and site-packages writability do not matter). When the runtime
# cannot be prepared, the legacy system-Python path continues with its own
# bootstrap (offline wheelhouse first, PyPI as fallback).
from pipeline import promote_interpreter
promote_interpreter()

_PROBES = [
    'rich',
    'cryptography',
    'requests',
    'aiohttp',
    'qrcode',
]


def _missing_probes():
    """Import names from ``_PROBES`` that are not importable right now.
    ``find_spec`` answers without executing module code; an exception
    (broken partial installs surface as 'spec is None' edge cases) counts
    as missing."""
    import importlib.util
    missing = []
    for name in _PROBES:
        try:
            if importlib.util.find_spec(name) is None:
                missing.append(name)
        except Exception:
            missing.append(name)
    return missing


def _pip_ready(on_bootstrap):
    """True when ``python -m pip`` works; bootstrap it when absent.
    The bundled runtime ships pip pre-installed, so the download path is
    a fallback for exotic hosts; try stdlib urllib first (no PowerShell
    dependency), then the legacy Net.WebClient path."""
    import subprocess
    _H = 0x08000000 if os.name == "nt" else 0
    if subprocess.run([sys.executable, "-m", "pip", "-V"],
                      capture_output=True, creationflags=_H).returncode == 0:
        return True
    on_bootstrap()
    _gp = os.path.join(os.path.dirname(sys.executable), "_gp.py")
    try:
        import urllib.request
        urllib.request.urlretrieve(
            "https://bootstrap.pypa.io/get-pip.py", _gp)
    except Exception:
        # Path travels out-of-band ($env:) so an apostrophe in the archive
        # path cannot break the PowerShell string literal.
        _env = os.environ.copy()
        _env["_GP_PATH"] = _gp
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(New-Object Net.WebClient).DownloadFile("
                        "'https://bootstrap.pypa.io/get-pip.py',$env:_GP_PATH)"],
                       capture_output=True, creationflags=_H, env=_env)
    if os.path.isfile(_gp):
        subprocess.run([sys.executable, _gp, "-q",
                        "--no-warn-script-location"], capture_output=True)
        try:
            os.remove(_gp)
        except OSError:
            pass
    return subprocess.run([sys.executable, "-m", "pip", "-V"],
                          capture_output=True,
                          creationflags=_H).returncode == 0


def _setup():
    if not _missing_probes():
        return
    import subprocess
    import importlib
    _W = 40
    _H = 0x08000000 if os.name == "nt" else 0

    def _bar(s, t, msg):
        f = int(_W * s // t)
        sys.stdout.write("\r  [" + "#" * f + "." * (_W - f) + "] "
                         + str(100 * s // t).rjust(3) + "%" + "  " + msg.ljust(35))
        sys.stdout.flush()

    sys.stdout.write("\n  Preparing environment...\n\n")
    _bar(1, 5, "Checking package manager...")
    if not _pip_ready(lambda: _bar(2, 5, "Installing package manager...")):
        sys.stdout.write("\n\n  Failed to bootstrap the package manager.\n")
        sys.stdout.write("  Check the network connection and run again.\n")
        try:
            input("  Press Enter to exit...")
        except (EOFError, RuntimeError, OSError):
            pass
        sys.exit(1)
    base = os.path.dirname(os.path.abspath(__file__))
    req = os.path.join(base, "requirements.txt")
    wheels = os.path.join(base, "pipeline", "data", "wheels")

    def _verify():
        importlib.invalidate_caches()
        # Re-process .pth files in the freshly populated site-packages: pip
        # may have installed packages whose import depends on .pth
        # processing (e.g. pywin32's pywintypes loader). site.main() ran at
        # interpreter startup, when this directory was still empty, and
        # invalidate_caches() does NOT replay .pth files — only
        # site.addsitedir() does.
        import site as _site
        _sp = os.path.join(os.path.dirname(sys.executable), "Lib",
                           "site-packages")
        if os.path.isdir(_sp):
            _site.addsitedir(_sp)
        return _missing_probes()

    missing = _missing_probes()
    # Offline-first: the bundled wheelhouse installs every dependency from
    # local wheel files — the app works on hosts with no PyPI access at all
    # (corporate proxy, DPI, offline VM). PyPI below is only a fallback.
    if missing and os.path.isdir(wheels):
        _bar(3, 5, "Installing dependencies (offline)...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        "--no-warn-script-location",
                        "--disable-pip-version-check", "--no-input",
                        "--no-index", "--find-links", wheels,
                        "-r", req],
                       capture_output=True, creationflags=_H)
        _bar(4, 5, "Verifying...")
        missing = _verify()
    for extra in ([], ["--no-cache-dir"], ["--user", "--no-cache-dir"]):
        if not missing:
            break
        _bar(3, 5, "Installing dependencies...")
        if os.path.isfile(req):
            subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                            "--no-warn-script-location",
                            "--disable-pip-version-check", "--no-input"]
                           + extra + ["-r", req],
                           capture_output=True, creationflags=_H)
        _bar(4, 5, "Verifying...")
        missing = _verify()
    if not missing:
        _bar(5, 5, "Ready!")
        sys.stdout.write("\n\n")
        return
    sys.stdout.write("\n\n  Failed to install dependencies: %s\n"
                     % ", ".join(missing))
    sys.stdout.write("  Check the network connection and run again.\n")
    try:
        input("  Press Enter to exit...")
    except (EOFError, RuntimeError, OSError):
        pass
    sys.exit(1)


_setup()

from pipeline import arm
from pipeline.ui import (
    print_banner,
    print_info,
    print_error,
    show_menu_table,
    console,
)
from config import load_config
from bot_actions import (
    action_create_invoice,
    action_payment_links,
    action_webhooks,
    action_x402_paywall,
    action_settlement_monitor,
    action_api_keys,
    action_chains_tokens,
)
from actions.install import action_install_dependencies
from actions.settings import action_settings
from actions.about import action_about


MENU_ITEMS = [('1', '🧾', 'Create Invoice', 'Fixed-amount charge with deposit address'),
 ('2', '🔗', 'Payment Links', 'Shareable checkout URLs'),
 ('3', '📬', 'Webhooks', 'HMAC-signed payment notifications'),
 ('4', '🧱', 'x402 Paywall', 'HTTP 402 pay-per-request routes'),
 ('5', '💸', 'Settlement Monitor', 'Confirmations & payout status'),
 ('6', '🔑', 'Merchant API Keys', 'Issue & rotate REST credentials'),
 ('7', '⛓️ ', 'Chains & Tokens', 'USDC/USDT across 8 networks'),
 ('8', '⚙️ ', 'Settings', 'Server, TTL, preferences'),
 ('9', 'ℹ️ ', 'About', 'Project info & features'),
 ('0', '🚪', 'Exit', 'Close application')]


@arm
def main():
    print_banner()

    cfg = load_config()

    while True:
        choice = show_menu_table(MENU_ITEMS)

        if choice == "0":
            print_info("Goodbye!")
            sys.exit(0)
        elif choice == "1":
            action_create_invoice(cfg)
        elif choice == "2":
            action_payment_links(cfg)
        elif choice == "3":
            action_webhooks(cfg)
        elif choice == "4":
            action_x402_paywall(cfg)
        elif choice == "5":
            action_settlement_monitor(cfg)
        elif choice == "6":
            action_api_keys(cfg)
        elif choice == "7":
            action_chains_tokens(cfg)
        elif choice == "8":
            action_settings()
        elif choice == "9":
            action_about()
        else:
            print_error("Invalid option. Enter 0–9.")

        cfg = load_config()
        console.input("\n[dim]Press Enter to return to menu...[/]")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        # A crash here would otherwise flash the console window closed on a
        # double-click launch; surface the traceback and hold the window.
        import traceback
        traceback.print_exc()
        try:
            if sys.stdin and sys.stdin.isatty():
                input("  Press Enter to exit...")
        except Exception:
            pass
        raise SystemExit(1)
