"""Celery worker or beat entrypoint. CELERY_APP and CELERY_OPTS select which."""

from __future__ import annotations

import importlib
import os
import sys


def get_app():
    app_path = os.environ.get("CELERY_APP")
    if not app_path:
        print("Error: CELERY_APP environment variable is not set.")
        sys.exit(1)

    try:
        if ":" in app_path:
            module_name, app_attr = app_path.split(":", 1)
        else:
            module_name, app_attr = app_path.rsplit(".", 1)

        module = importlib.import_module(module_name)
        return getattr(module, app_attr)
    except Exception as exc:
        print(f"Error loading Celery app '{app_path}': {exc}")
        sys.exit(1)


def main() -> None:
    celery_app = get_app()
    opts = os.environ.get("CELERY_OPTS", "worker --loglevel=info").split()
    print(f"Starting Celery with options: {opts}")
    celery_app.start(argv=opts)


if __name__ == "__main__":
    main()
