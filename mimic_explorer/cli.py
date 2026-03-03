"""
Entry point for `mimic-explorer` command.
Installed via pyproject.toml console_scripts.
"""
import argparse
import os
import sys
import socket
import threading
import webbrowser
import time

VERSION = '0.1.0'


def find_available_port(start=8000, end=9000):
    """Find the first available port in the given range."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return start


def open_browser(port, delay=1.5):
    """Open browser after a short delay to let the server start."""
    time.sleep(delay)
    webbrowser.open(f'http://localhost:{port}')


def run_tests():
    """Run the built-in test suite to verify the installation."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimic_explorer.settings')

    import django
    django.setup()

    from io import StringIO
    from django.core.management import call_command
    # Route stdout to devnull to suppress Django's "System check" message
    devnull = StringIO()
    old_stdout = sys.stdout
    sys.stdout = devnull
    try:
        call_command('test', 'tests', testrunner='tests.runner.MIMICTestRunner',
                     verbosity=0, stdout=devnull)
    finally:
        sys.stdout = old_stdout


def main():
    parser = argparse.ArgumentParser(
        prog='mimic-explorer',
        description='MIMIC Explorer — a locally installable EHR research sandbox for MIMIC-IV',
    )
    parser.add_argument(
        '--version', '-V',
        action='version',
        version=f'mimic-explorer {VERSION}',
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run the built-in test suite to verify your installation',
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=None,
        help='Port to run the server on (default: auto-detect)',
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not open the browser automatically',
    )
    args = parser.parse_args()

    if args.test:
        # Suppress Django system check output
        import logging
        logging.getLogger('django').setLevel(logging.CRITICAL)
        run_tests()
        return

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimic_explorer.settings')

    import django
    django.setup()

    from django.core.management import call_command

    # Run migrations silently
    call_command('migrate', verbosity=0)

    # Ensure DuckDB schema exists
    from core.duckdb_manager import get_connection
    from core.duckdb_schema import ensure_schema
    ensure_schema(get_connection())

    # Collect static files silently
    call_command('collectstatic', verbosity=0, interactive=False)

    # Check if import has been completed
    from core.models import SystemConfig
    config = SystemConfig.get_solo()

    port = args.port or find_available_port()

    if config.import_status != 'completed':
        url_path = '/setup'
    else:
        url_path = '/'

    print(f"\n  MIMIC Explorer v{VERSION}")
    print(f"  Open http://localhost:{port}{url_path} in your browser")
    print(f"  Press Ctrl+C to stop\n")

    # Open browser in daemon thread
    if not args.no_browser:
        browser_thread = threading.Thread(
            target=open_browser,
            args=(port,),
            daemon=True
        )
        browser_thread.start()

    # Start Django dev server
    from django.core.management import execute_from_command_line
    sys.argv = ['manage.py', 'runserver', f'127.0.0.1:{port}', '--noreload']
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
