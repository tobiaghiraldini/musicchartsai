from django.core.management.base import BaseCommand
from apps.soundcharts.tasks import process_scheduled_chart_syncs


class Command(BaseCommand):
    help = 'Process scheduled chart syncs'

    def handle(self, *args, **options):
        self.stdout.write('Processing scheduled chart syncs...')
        try:
            result = process_scheduled_chart_syncs()
            if result:
                self.stdout.write(
                    self.style.SUCCESS('Successfully processed chart sync schedules')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No chart sync schedules were processed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing chart sync schedules: {e}')
            )
