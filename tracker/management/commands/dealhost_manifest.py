import json
import os

from django.core.management.base import BaseCommand, CommandError

from tracker.dealhost import build_dealhost_runtime_manifest, load_dealhost_sdk


class Command(BaseCommand):
    help = 'Print Dealhost deployment metadata and optionally verify the configured SDK module.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sdk-check',
            action='store_true',
            help='Import the configured Dealhost SDK module and fail if it is unavailable.',
        )

    def handle(self, *args, **options):
        manifest = build_dealhost_runtime_manifest(os.environ)
        if options['sdk_check']:
            module_name = str(manifest['sdk']['module'])
            try:
                sdk_module = load_dealhost_sdk(module_name)
            except RuntimeError as exc:
                raise CommandError(str(exc)) from exc
            manifest['sdk']['loaded'] = True
            manifest['sdk']['module_file'] = getattr(sdk_module, '__file__', None)
        self.stdout.write(json.dumps(manifest, indent=2, ensure_ascii=False))
