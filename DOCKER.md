## Wymagania

- Docker 20.10+
- Docker Compose 2.0+


### 1. Uruchomienie z Docker Compose

```bash
git clone <repository-url>
cd Scrapper

docker-compose up --build

```

### 2. Uruchomienie tylko bazy danych PostgreSQL

```bash

docker-compose up db

```

## Zmienne środowiskowe

```yaml
environment:
  - DEBUG=1
  - DATABASE_URL=postgresql://crawler_user:crawler_password@db:5432/crawler_db
  - SECRET_KEY=django-insecure-docker-secret-key-change-in-production
```

### Porty

- 8000 - Aplikacja Django
- 5432 - PostgreSQL

### Wolumeny

- `postgres_data` - Dane PostgreSQL
- `static_volume` - Statyczne pliki Django

## Serwisy

### `web` - Aplikacja Django
- Automatycznie uruchamia migracje
- Zbiera statyczne pliki
- Uruchamia serwer deweloperski

### `db` - PostgreSQL
- Baza danych PostgreSQL 15
- Automatyczne tworzenie bazy `crawler_db`
- Health check

### `scraper` - Scraper
- Uruchamia scrapowanie artykułów
- Dostępny przez profil `scraping`

## Uruchomienie Scrapera

### Opcja 1: W kontenerze

```bash
docker-compose --profile scraping up scraper
```

### Opcja 2: W kontenerze web

```bash
docker-compose exec web python manage.py scrape_articles --verbose
```

### Testy

```bash
docker-compose exec web python manage.py test
```

### Shell Django

```bash
docker-compose exec web python manage.py shell
```

### Baza danych

```bash
docker-compose exec db psql -U crawler_user -d crawler_db
```

### Zmiana portów

Edytuj `docker-compose.yml`:

```yaml
services:
  web:
    ports:
      - "8080:8000"
```

### Zmiana bazy danych

Edytuj zmienne środowiskowe:

```yaml
environment:
  - DATABASE_URL=postgresql://user:password@db:5432/database_name
```

### Dodanie nowych zależności

1. Dodaj do `requirements.txt`
2. Przebuduj kontener: `docker-compose build web`


### Bezpieczne ustawienia

```yaml
environment:
  - DEBUG=0
  - SECRET_KEY=your-secret-key-here
  - ALLOWED_HOSTS=your-domain.com
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```