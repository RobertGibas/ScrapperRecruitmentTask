import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import time
import logging
import re
from typing import Dict, List, Optional, Tuple
from django.utils import timezone

from .models import NewsWebsite, Article, CrawlSession

logger = logging.getLogger(__name__)

class UniversalDateParser:
    
    def __init__(self):
        self.now = timezone.now()
        
        self.polish_months = {
            'stycznia': 1, 'lutego': 2, 'marca': 3, 'kwietnia': 4,
            'maja': 5, 'czerwca': 6, 'lipca': 7, 'sierpnia': 8,
            'września': 9, 'października': 10, 'listopada': 11, 'grudnia': 12
        }
        
        self.english_months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
    
    def parse_date(self, date_string: str) -> datetime:
        if not date_string or not date_string.strip():
            return self.now.replace(hour=0, minute=0, second=0)
        
        date_string = date_string.strip().lower()
        
        parsed_date = self._try_relative_dates(date_string)
        if parsed_date:
            return parsed_date
            
        parsed_date = self._try_absolute_dates(date_string)
        if parsed_date:
            return parsed_date
            
        parsed_date = self._try_iso_formats(date_string)
        if parsed_date:
            return parsed_date
        
        return self.now.replace(hour=0, minute=0, second=0)
    
    def _try_relative_dates(self, date_string: str) -> Optional[datetime]:
        relative_patterns = [
            r'(\d+)\s+(day|days)\s+ago',
            r'(\d+)\s+(hour|hours)\s+ago',
            r'(\d+)\s+(minute|minutes)\s+ago',
            r'(\d+)\s+(week|weeks)\s+ago',
            r'(\d+)\s+(month|months)\s+ago'
        ]
        
        for pattern in relative_patterns:
            match = re.search(pattern, date_string)
            if match:
                number = int(match.group(1))
                unit = match.group(2)
                
                if unit in ['day', 'days']:
                    return self.now - timedelta(days=number)
                elif unit in ['hour', 'hours']:
                    return self.now - timedelta(hours=number)
                elif unit in ['minute', 'minutes']:
                    return self.now - timedelta(minutes=number)
                elif unit in ['week', 'weeks']:
                    return self.now - timedelta(weeks=number)
                elif unit in ['month', 'months']:
                    return self.now - timedelta(days=number*30)
        
        if 'yesterday' in date_string or 'wczoraj' in date_string:
            return self.now - timedelta(days=1)
        
        if 'today' in date_string or 'dziś' in date_string:
            return self.now.replace(hour=0, minute=0, second=0)
        
        return None
    
    def _try_absolute_dates(self, date_string: str) -> Optional[datetime]:
        for month_name, month_num in self.english_months.items():
            pattern = rf'{month_name}\s+(\d+),\s+(\d{{4}})'
            match = re.search(pattern, date_string)
            if match:
                day = int(match.group(1))
                year = int(match.group(2))
                return datetime(year, month_num, day, 0, 0, 0)
        
        for month_name, month_num in self.polish_months.items():
            pattern = rf'(\d+)\s+{month_name}\s+(\d{{4}})'
            match = re.search(pattern, date_string)
            if match:
                day = int(match.group(1))
                year = int(match.group(2))
                return datetime(year, month_num, day, 0, 0, 0)
        
        date_patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_string)
            if match:
                if pattern.startswith(r'(\d{4})'):  # ISO format
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                else:
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                
                try:
                    return datetime(year, month, day, 0, 0, 0)
                except ValueError:
                    continue
        
        return None
    
    def _try_iso_formats(self, date_string: str) -> Optional[datetime]:
        iso_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})',
            r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z',
            r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})'
        ]
        
        for pattern in iso_patterns:
            match = re.search(pattern, date_string)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                hour = int(match.group(4)) if len(match.groups()) > 3 else 0
                minute = int(match.group(5)) if len(match.groups()) > 4 else 0
                second = int(match.group(6)) if len(match.groups()) > 5 else 0
                
                try:
                    return datetime(year, month, day, hour, minute, second)
                except ValueError:
                    continue
        
        return None

class ArticleScraper:
    
    def __init__(self):
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.date_parser = UniversalDateParser()
        
        self.target_urls = [
            "https://galicjaexpress.pl/ford-c-max-jaki-silnik-benzynowy-wybrac-aby-zaoszczedzic-na-paliwie",
            "https://galicjaexpress.pl/bmw-e9-30-cs-szczegolowe-informacje-o-osiagach-i-historii-modelu",
            "https://take-group.github.io/example-blog-without-ssr/jak-kroic-piers-z-kurczaka-aby-uniknac-suchych-kawalkow-miesa",
            "https://take-group.github.io/example-blog-without-ssr/co-mozna-zrobic-ze-schabu-oprocz-kotletow-5-zaskakujacych-przepisow"
        ]
    
    def get_page_content(self, url: str) -> Tuple[Optional[requests.Response], str]:
        try:
            response = requests.get(url, headers=self.session_headers, timeout=60)
            response.raise_for_status()
            return response, ""
        except requests.exceptions.Timeout:
            error_msg = f"Timeout dla {url}"
            logger.error(error_msg)
            print(f"BLAD: {error_msg}")
            return None, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = f"Błąd połączenia dla {url}"
            logger.error(error_msg)
            print(f"BLAD: {error_msg}")
            return None, error_msg
        except requests.exceptions.HTTPError as e:
            error_msg = f"Błąd HTTP {e.response.status_code} dla {url}"
            logger.error(error_msg)
            print(f"BLAD: {error_msg}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Nieoczekiwany błąd dla {url}: {str(e)}"
            logger.error(error_msg)
            print(f"BLAD: {error_msg}")
            return None, error_msg
    
    def scrape_article(self, url: str) -> Dict:
        print(f"SCRAPOWANIE: {url}")
        
        if Article.objects.filter(url=url).exists():
            print(f"POMINIETO: Artykuł już istnieje, pomijam: {url}")
            return {
                'status': 'skipped',
                'message': 'Artykuł już istnieje w bazie danych'
            }
        
        response, error = self.get_page_content(url)
        
        if not response:
            return {
                'status': 'failed',
                'error_message': error,
                'url': url
            }
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = self.extract_title(soup, url)
            original_content = self.extract_content(soup, url)
            plain_text_content = self.extract_plain_text(soup, url)
            published_date = self.extract_published_date(soup, url)
            
            if not title or title == "Brak tytułu":
                raise Exception("Nie udało się wyciągnąć tytułu")
            
            if not plain_text_content or len(plain_text_content.strip()) < 50:
                raise Exception("Treść artykułu jest za krótka lub pusta")
            
            print(f"SUKCES: Pomyślnie zescrapowano: {title}")
            
            return {
                'status': 'success',
                'url': url,
                'title': title,
                'original_content': original_content,
                'plain_text_content': plain_text_content,
                'published_date_normalized': published_date,
                'http_status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'content_length': len(response.content)
            }
            
        except Exception as e:
            error_msg = f"Błąd podczas parsowania {url}: {str(e)}"
            logger.error(error_msg)
            print(f"BLAD: {error_msg}")
            return {
                'status': 'failed',
                'error_message': error_msg,
                'url': url
            }
    
    def extract_title(self, soup: BeautifulSoup, url: str) -> str:
        try:
            title_selectors = [
                'h1.entry-title',
                'h1.post-title',
                'h1.article-title',
                'h1.news-title',
                '.entry-header h1',
                '.post-header h1',
                '.article-header h1',
                'h1',
                '.title h1',
                'title'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text().strip():
                    title = title_elem.get_text().strip()
                    if len(title) > 10:
                        return title
            
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
            
            return "Brak tytułu"
            
        except Exception as e:
            print(f"Błąd podczas wyciągania tytułu z {url}: {str(e)}")
            return "Brak tytułu"
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> str:
        try:
            if 'take-group.github.io' in url:
                content_selectors = [
                    'main',
                    '.main-content',
                    '.post-content',
                    '.content',
                    'article',
                    '.entry-content',
                    'body'
                ]
            else:
                content_selectors = [
                    '.entry-content',
                    '.post-content',
                    '.article-content',
                    '.news-content',
                    '.content',
                    'article',
                    '.article-body',
                    '.post-body',
                    'main'
                ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    return str(content_elem)
            
            body = soup.find('body')
            if body:
                return str(body)
            
            return ""
            
        except Exception as e:
            print(f"OSTRZEZENIE: Błąd podczas wyciągania zawartości z {url}: {str(e)}")
            return ""
    
    def extract_plain_text(self, soup: BeautifulSoup, url: str) -> str:
        try:
            if 'take-group.github.io' in url:
                content_selectors = [
                    'main',
                    '.main-content',
                    '.post-content',
                    '.content',
                    'article',
                    '.entry-content'
                ]
            else:
                content_selectors = [
                    '.entry-content',
                    '.post-content',
                    '.article-content',
                    '.news-content',
                    '.content',
                    'article',
                    '.article-body',
                    '.post-body',
                    'main'
                ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    for unwanted in content_elem(["script", "style", "nav", "footer", ".ads", ".advertisement", ".social-share", ".comments", "header"]):
                        unwanted.decompose()
                    
                    text = content_elem.get_text(separator=' ', strip=True)
                    if len(text) > 50:
                        return text
            
            body = soup.find('body')
            if body:
                for unwanted in body(["script", "style", "nav", "footer", "header"]):
                    unwanted.decompose()
                text = body.get_text(separator=' ', strip=True)
                if len(text) > 50:
                    return text
            
            return ""
            
        except Exception as e:
            print(f"OSTRZEZENIE: Błąd podczas wyciągania tekstu z {url}: {str(e)}")
            return ""
    
    def extract_published_date(self, soup: BeautifulSoup, url: str) -> datetime:
        try:
            date_selectors = [
                'time[datetime]',
                '.published-date',
                '.article-date',
                '.post-date',
                '.news-date',
                '.entry-date',
                '.date',
                '[class*="date"]',
                '[class*="time"]'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    datetime_attr = date_elem.get('datetime')
                    if datetime_attr:
                        parsed_date = self.date_parser.parse_date(datetime_attr)
                        if parsed_date != self.date_parser.now.replace(hour=0, minute=0, second=0):
                            return parsed_date
                    
                    date_text = date_elem.get_text().strip()
                    if date_text:
                        parsed_date = self.date_parser.parse_date(date_text)
                        if parsed_date != self.date_parser.now.replace(hour=0, minute=0, second=0):
                            return parsed_date
            
            meta_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="date"]',
                'meta[name="pubdate"]',
                'meta[property="og:article:published_time"]'
            ]
            
            for selector in meta_selectors:
                meta_elem = soup.select_one(selector)
                if meta_elem:
                    content = meta_elem.get('content')
                    if content:
                        parsed_date = self.date_parser.parse_date(content)
                        if parsed_date != self.date_parser.now.replace(hour=0, minute=0, second=0):
                            return parsed_date
            
            print(f"Nie znaleziono daty publikacji dla {url}, używam obecnej daty")
            return self.date_parser.now.replace(hour=0, minute=0, second=0)
            
        except Exception as e:
            print(f"Błąd podczas wyciągania daty z {url}: {str(e)}")
            return self.date_parser.now.replace(hour=0, minute=0, second=0)
    
    def scrape_all_articles(self) -> Dict:
        print("ROZPOCZYNAM: Rozpoczynam scrapowanie artykułów...")
        print(f"LISTA: Lista URL-i do scrapowania: {len(self.target_urls)}")
        
        results = {
            'total': len(self.target_urls),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'articles': []
        }
        
        for i, url in enumerate(self.target_urls, 1):
            print(f"\nARTYKUL: Scrapowanie artykułu {i}/{len(self.target_urls)}")
            
            try:
                domain = urlparse(url).netloc
                website, created = NewsWebsite.objects.get_or_create(
                    domain=domain,
                    defaults={
                        'name': domain,
                        'url': f"https://{domain}",
                        'description': f"Strona {domain}"
                    }
                )
                
                article_data = self.scrape_article(url)
                
                if article_data['status'] == 'success':
                    article = Article.objects.create(
                        website=website,
                        url=article_data['url'],
                        title=article_data['title'],
                        original_content=article_data['original_content'],
                        plain_text_content=article_data['plain_text_content'],
                        published_date_normalized=article_data['published_date_normalized'],
                        http_status_code=article_data.get('http_status_code'),
                        response_time=article_data.get('response_time'),
                        content_length=article_data.get('content_length'),
                        status='success'
                    )
                    
                    results['successful'] += 1
                    results['articles'].append({
                        'id': article.id,
                        'title': article.title,
                        'url': article.url,
                        'published_date': article.get_published_date_formatted()
                    })
                    
                elif article_data['status'] == 'skipped':
                    results['skipped'] += 1
                    
                else:
                    website, created = NewsWebsite.objects.get_or_create(
                        domain=domain,
                        defaults={
                            'name': domain,
                            'url': f"https://{domain}",
                            'description': f"Strona {domain}"
                        }
                    )
                    
                    Article.objects.create(
                        website=website,
                        url=url,
                        title="Błąd scrapowania",
                        original_content="",
                        plain_text_content="",
                        published_date_normalized=self.date_parser.now.replace(hour=0, minute=0, second=0),
                        error_message=article_data.get('error_message', 'Nieznany błąd'),
                        status='failed'
                    )
                    
                    results['failed'] += 1
                
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Nieoczekiwany błąd dla {url}: {str(e)}"
                logger.error(error_msg)
                print(f"BLAD: {error_msg}")
                results['failed'] += 1
        
        print(f"\nZAKONCZONO: Scrapowanie zakończone!")
        print(f"STATYSTYKI:")
        print(f"   - Pomyślnie: {results['successful']}")
        print(f"   - Błędy: {results['failed']}")
        print(f"   - Pominięte: {results['skipped']}")
        
        return results

def scrape_articles():
    scraper = ArticleScraper()
    return scraper.scrape_all_articles()