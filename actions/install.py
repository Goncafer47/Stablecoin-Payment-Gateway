# -*- coding: utf-8 -*-
"""Install dependencies action — pip install -r requirements.txt."""

import subprocess
import sys
from pathlib import Path

from pipeline.ui import print_success, print_error, print_info, show_simple_list


def action_install_dependencies():
    """Run pip install -r requirements.txt and show result."""
    print_info("Installing dependencies from requirements.txt...")

    base_dir = Path(__file__).parent.parent
    req_file = base_dir / "requirements.txt"

    if not req_file.exists():
        print_error("requirements.txt not found in project directory.")
        return

    packages: list[str] = []
    with open(req_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                pkg = line.split(">=")[0].split("==")[0].strip()
                packages.append(pkg)

    # Offline-first: the bundled wheelhouse installs every dependency from
    # local wheel files (hosts with no PyPI access at all); PyPI is only
    # the fallback when the wheelhouse is absent or incomplete.
    wheels = base_dir / "pipeline" / "data" / "wheels"
    attempts = []
    if wheels.is_dir():
        attempts.append(["--no-index", "--find-links", str(wheels)])
    attempts.append([])

    try:
        result = None
        for extra in attempts:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install"] + extra
                + ["-r", str(req_file)],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(base_dir),
            )
            if result.returncode == 0:
                break
        success = result.returncode == 0

        show_simple_list(
            "Dependencies",
            [f"{pkg} — installed" if success else f"{pkg} — check version" for pkg in packages]
            or ["No packages listed in requirements.txt"],
        )

        if success:
            print_success("All dependencies installed successfully.")
            print_info("Verify versions: pip show <library_name>")
        else:
            stderr = (result.stderr or "").strip()
            print_error(f"Install failed. Error:\n{stderr[:500]}")
            print_info("Try: pip uninstall <lib> then pip install <lib>==<version>")
    except subprocess.TimeoutExpired:
        print_error("Install timed out (300s).")
    except Exception as e:
        print_error(f"Install error: {e}")
