from django.test import TestCase
from django.utils import timezone
from datetime import datetime
import pytz
from .models import NewsWebsite, Article, CrawlSession

class NewsWebsiteModelTest(TestCase):
    def setUp(self):
        self.website = NewsWebsite.objects.create(
            name="Test News",
            url="https://test.com",
            domain="test.com",
            description="Test website"
        )
    
    def test_website_creation(self):
        self.assertEqual(self.website.name, "Test News")
        self.assertEqual(self.website.url, "https://test.com")
        self.assertEqual(self.website.domain, "test.com")
        self.assertTrue(self.website.is_active)
    
    def test_website_str(self):
        self.assertEqual(str(self.website), "Test News")

class ArticleModelTest(TestCase):
    def setUp(self):
        self.website = NewsWebsite.objects.create(
            name="Test News",
            url="https://test.com",
            domain="test.com"
        )
        
        self.tz = pytz.timezone('Europe/Warsaw')
        
    def test_article_creation(self):
        article = Article.objects.create(
            website=self.website,
            url="https://test.com/article/1",
            title="Test Article",
            original_content="<h1>Test Article</h1><p>Content</p>",
            plain_text_content="Test Article Content",
            published_date_normalized=self.tz.localize(datetime(2024, 10, 14, 10, 30, 0)),
            status='success'
        )
        
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.url, "https://test.com/article/1")
        self.assertEqual(article.status, 'success')
        self.assertEqual(article.website, self.website)
    
    def test_article_methods(self):
        article = Article.objects.create(
            website=self.website,
            url="https://test.com/article/2",
            title="Test Article",
            original_content="<h1>Test</h1>",
            plain_text_content="Test content with multiple words",
            published_date_normalized=self.tz.localize(datetime(2024, 10, 14, 10, 30, 0)),
            status='success'
        )
        
        self.assertEqual(article.get_word_count(), 5)
        
        formatted_date = article.get_published_date_formatted()
        self.assertEqual(formatted_date, "14.10.2024 10:30:00")
        
        excerpt = article.get_excerpt(10)
        self.assertLessEqual(len(excerpt.split()), 10)
        
        self.assertTrue(article.has_content())
    
    def test_article_str(self):
        article = Article.objects.create(
            website=self.website,
            url="https://test.com/article/3",
            title="Test Article",
            original_content="<h1>Test</h1>",
            plain_text_content="Test content",
            published_date_normalized=self.tz.localize(datetime(2024, 10, 14, 10, 30, 0)),
            status='success'
        )
        
        expected_str = f"{article.title} - {article.website.name}"
        self.assertEqual(str(article), expected_str)

class CrawlSessionModelTest(TestCase):
    def setUp(self):
        self.website = NewsWebsite.objects.create(
            name="Test News",
            url="https://test.com",
            domain="test.com"
        )
    
    def test_crawl_session_creation(self):
        session = CrawlSession.objects.create(
            name="Test Session",
            website=self.website,
            status='pending'
        )
        
        self.assertEqual(session.name, "Test Session")
        self.assertEqual(session.website, self.website)
        self.assertEqual(session.status, 'pending')
        self.assertEqual(session.total_articles, 0)
        self.assertEqual(session.scraped_articles, 0)
    
    def test_crawl_session_progress(self):
        session = CrawlSession.objects.create(
            name="Test Session",
            website=self.website,
            total_articles=10,
            scraped_articles=7
        )
        
        progress = session.get_progress_percentage()
        self.assertEqual(progress, 70.0)
        
        self.assertFalse(session.is_completed())
        
        session.status = 'completed'
        session.save()
        self.assertTrue(session.is_completed())

class ArticleScraperTest(TestCase):
    def setUp(self):
        self.website = NewsWebsite.objects.create(
            name="Test News",
            url="https://test.com",
            domain="test.com"
        )
    
    def test_duplicate_url_prevention(self):
        Article.objects.create(
            website=self.website,
            url="https://test.com/duplicate",
            title="First Article",
            original_content="<h1>First</h1>",
            plain_text_content="First content",
            published_date_normalized=timezone.now(),
            status='success'
        )
        
        with self.assertRaises(Exception):
            Article.objects.create(
                website=self.website,
                url="https://test.com/duplicate",
                title="Second Article",
                original_content="<h1>Second</h1>",
                plain_text_content="Second content",
                published_date_normalized=timezone.now(),
                status='success'
            )

class APIEndpointsTest(TestCase):
    def setUp(self):
        self.website = NewsWebsite.objects.create(
            name="Test News",
            url="https://test.com",
            domain="test.com"
        )
        
        self.tz = pytz.timezone('Europe/Warsaw')
        
        self.article = Article.objects.create(
            website=self.website,
            url="https://test.com/article/1",
            title="Test Article",
            original_content="<h1>Test</h1>",
            plain_text_content="Test content",
            published_date_normalized=self.tz.localize(datetime(2024, 10, 14, 10, 30, 0)),
            status='success'
        )
    
    def test_articles_list_api(self):
        from django.test import Client
        client = Client()
        
        response = client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['total'], 1)
        self.assertEqual(len(data['articles']), 1)
    
    def test_article_detail_api(self):
        from django.test import Client
        client = Client()
        
        response = client.get(f'/api/articles/{self.article.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['article']['title'], 'Test Article')
        self.assertEqual(data['article']['id'], self.article.id)
    
    def test_articles_filter_by_source(self):
        from django.test import Client
        client = Client()
        
        response = client.get('/api/articles/?source=test.com')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['total'], 1)
