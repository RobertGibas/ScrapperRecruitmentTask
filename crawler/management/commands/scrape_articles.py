from django.core.management.base import BaseCommand
from crawler.scraper import scrape_articles
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Command(BaseCommand):
    help = 'Scrapuje artykuły z określonych URL-i'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Szczegółowe wyświetlanie informacji',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS('Rozpoczynam scrapowanie artykulow...')
            )
        
        try:
            results = scrape_articles()
            
            self.stdout.write(
                self.style.SUCCESS('Scrapowanie zakonczone!')
            )
            
            self.stdout.write('Statystyki:')
            self.stdout.write(f'   - Calkowita liczba URL: {results["total"]}')
            self.stdout.write(f'   - Pomyslnie zescrapowane: {results["successful"]}')
            self.stdout.write(f'   - Bledy: {results["failed"]}')
            self.stdout.write(f'   - Pominiete (duplikaty): {results["skipped"]}')
            
            if results['articles']:
                self.stdout.write('\nZescrapowane artykuly:')
                for article in results['articles']:
                    self.stdout.write(
                        f'   - ID: {article["id"]} | {article["title"]} | {article["published_date"]}'
                    )
            
            if results['failed'] > 0:
                self.stdout.write(
                    self.style.WARNING(f'{results["failed"]} artykulow nie zostalo zescrapowanych')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Blad podczas scrapowania: {str(e)}')
            )
            raise
