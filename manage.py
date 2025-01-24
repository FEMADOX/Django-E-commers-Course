"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks.

    Raises:
        ImportError: If Django is not installed or not available on PYTHONPATH.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edshop.settings")
    try:
        from django.core.management import execute_from_command_line  # noqa: PLC0415
    except ImportError as exc:
        msg = (
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )
        raise ImportError(
            msg,
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
