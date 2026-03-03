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
    parser.add_argument(
        '--data',
        type=str,
        default=None,
        metavar='PATH',
        help='Path to MIMIC-IV data folder — validates and imports on startup',
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

    # Handle --data flag: validate and import MIMIC-IV data
    if args.data:
        from core.importer import validate_mimic_folder, MIMICImporter
        from core.models import SystemConfig

        data_path = os.path.abspath(args.data)
        validation = validate_mimic_folder(data_path)
        if not validation['valid']:
            missing = ', '.join(validation['missing_required'])
            print(f"\n  Error: Invalid MIMIC-IV folder: {data_path}")
            print(f"  Missing required files: {missing}\n")
            sys.exit(1)

        config = SystemConfig.get_solo()
        if config.import_status == 'completed':
            print(f"\n  Data already imported. Use the web interface to supplement import.")
            print(f"  To reimport, run: mimic-explorer  (then use Reset in the UI)\n")
        else:
            # Detect available modules
            modules = ['hosp']
            if validation['icu']:
                modules.append('icu')
            if validation['note']:
                modules.append('note')

            print(f"\n  Importing from: {data_path}")
            print(f"  Modules: {', '.join(modules)}")

            config.mimic_data_path = data_path
            config.save()

            importer = MIMICImporter(data_path, modules=modules)
            importer.run()

            config.refresh_from_db()
            total = config.import_progress.get('total_rows', 0)
            print(f"  Import complete! {total:,} rows imported.\n")

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
