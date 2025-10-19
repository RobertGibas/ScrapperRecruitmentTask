# Crawler Artykułów

System do scrapowania i zarządzania artykułami z różnych serwisów informacyjnych. Projekt zawiera REST API, interfejs web oraz Django management commands do automatyzacji procesu crawlowania.

##Stack Technologiczny

- Python 3.10+
- Django 5.x
- Django REST Framework 3.14+
- BeautifulSoup4 - parsowanie HTML
- Requests - HTTP requests
- LXML - XML/HTML parser
- SQLite (domyślnie) / PostgreSQL (opcjonalnie)

## Wymagania Funkcjonalne

### Zaimplementowane funkcjonalności:

1. Scraping artykułów z określonych URL-i
2. Uniwersalny parser dat - obsługuje różne formaty dat
3. Walidacja URL - unikanie duplikatów w bazie danych
4. REST API - pełne endpointy do zarządzania danymi
5. Django Management Command - automatyzacja scrapowania
6. Obsługa błędów - graceful handling i logowanie
7. Interfejs web - przeglądanie artykułów przez przeglądarkę
8. Eksport danych - CSV i JSON

## Instalacja i Uruchomienie

### 1. Klonowanie i przygotowanie środowiska

```bash
git clone <repository-url>
cd Scrapper

python -m venv venv
source venv/bin/activate  
venv\Scripts\activate     

pip install -r requirements.txt
```

### 2. Konfiguracja bazy danych

```bash
python manage.py makemigrations
python manage.py migrate

python manage.py createsuperuser
```

### 3. Uruchomienie serwera deweloperskiego

```bash
python manage.py runserver
```

Aplikacja będzie dostępna pod adresem: `http://127.0.0.1:8000/`

## Uruchomienie Scrapera

### Podstawowe scrapowanie

```bash
python manage.py scrape_articles
```

### Scrapowanie z szczegółowymi informacjami

```bash
python manage.py scrape_articles --verbose
```

### Co robi scraper:
- Scrapuje artykuły z 4 określonych URL-i
- Wyciąga: tytuł, treść (HTML i plain text), datę publikacji
- Normalizuje daty do formatu `dd.mm.yyyy HH:mm:ss`
- Sprawdza duplikaty i pomija istniejące artykuły
- Zapisuje wyniki do bazy danych
- Loguje błędy i postęp

## Konfiguracja

### Ustawienia Django (`scrapper/settings.py`)

Aplikacja używa domyślnych ustawień Django z SQLite. Dla produkcji zalecana jest zmiana na PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Dostosowanie scrapera

URL-e do scrapowania są zdefiniowane w `crawler/scraper.py`:

```python
self.target_urls = [
    "https://galicjaexpress.pl/ford-c-max-jaki-silnik-benzynowy-wybrac-aby-zaoszczedzic-na-paliwie",
    "https://galicjaexpress.pl/bmw-e9-30-cs-szczegolowe-informacje-o-osiagach-i-historii-modelu",
    "https://take-group.github.io/example-blog-without-ssr/jak-kroic-piers-z-kurczaka-aby-uniknac-suchych-kawalkow-miesa",
    "https://take-group.github.io/example-blog-without-ssr/co-mozna-zrobic-ze-schabu-oprocz-kotletow-5-zaskakujacych-przepisow"
]
```

## Testy

### Uruchomienie testów:

```bash
python manage.py test
```
