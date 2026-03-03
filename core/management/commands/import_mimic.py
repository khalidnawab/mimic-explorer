"""Management command for importing MIMIC-IV data."""
from django.core.management.base import BaseCommand, CommandError
from core.importer import MIMICImporter, validate_mimic_folder


class Command(BaseCommand):
    help = 'Import MIMIC-IV data from CSV files into the database'

    def add_arguments(self, parser):
        parser.add_argument('folder_path', type=str, help='Path to the MIMIC-IV data folder')
        parser.add_argument(
            '--modules', nargs='+', default=['hosp'],
            choices=['hosp', 'icu', 'note'],
            help='Modules to import (default: hosp)',
        )
        parser.add_argument(
            '--patient-limit', type=int, default=None,
            help='Limit number of patients to import',
        )
        parser.add_argument(
            '--generate-fhir', action='store_true',
            help='Generate FHIR resources during import',
        )

    def handle(self, *args, **options):
        folder_path = options['folder_path']

        # Validate folder
        self.stdout.write(f'Validating folder: {folder_path}')
        result = validate_mimic_folder(folder_path)
        if not result['valid']:
            raise CommandError(
                f"Invalid MIMIC folder. Missing required files: {result['missing_required']}"
            )
        self.stdout.write(self.style.SUCCESS('Folder validation passed'))

        # Run import
        importer = MIMICImporter(
            folder_path=folder_path,
            modules=options['modules'],
            patient_limit=options['patient_limit'],
            generate_fhir=options['generate_fhir'],
        )

        self.stdout.write('Starting import...')
        importer.run()
        self.stdout.write(self.style.SUCCESS('Import completed successfully!'))
