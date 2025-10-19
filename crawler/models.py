from django.db import models
from django.utils import timezone
from datetime import datetime

class NewsWebsite(models.Model):
    url = models.URLField(max_length=500, unique=True, verbose_name="URL strony")
    domain = models.CharField(max_length=200, blank=True, verbose_name="Domena")
    name = models.CharField(max_length=200, verbose_name="Nazwa serwisu")
    description = models.TextField(blank=True, verbose_name="Opis")
    is_active = models.BooleanField(default=True, verbose_name="Aktywna")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    
    class Meta:
        verbose_name = "Serwis informacyjny"
        verbose_name_plural = "Serwisy informacyjne"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class CrawlSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Oczekuje'),
        ('running', 'W trakcie'),
        ('completed', 'Zakończona'),
        ('failed', 'Błąd'),
        ('cancelled', 'Anulowana'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nazwa sesji")
    website = models.ForeignKey(NewsWebsite, on_delete=models.CASCADE, verbose_name="Serwis")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Rozpoczęto")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Zakończono")
    total_articles = models.PositiveIntegerField(default=0, verbose_name="Całkowita liczba artykułów")
    scraped_articles = models.PositiveIntegerField(default=0, verbose_name="Scrapowane artykuły")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    
    class Meta:
        verbose_name = "Sesja crawlowania"
        verbose_name_plural = "Sesje crawlowania"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.website.name}"
    
    def get_progress_percentage(self):
        if self.total_articles == 0:
            return 0
        return (self.scraped_articles / self.total_articles) * 100
    
    def is_completed(self):
        return self.status == 'completed'

class Article(models.Model):
    STATUS_CHOICES = [
        ('success', 'Sukces'),
        ('failed', 'Błąd'),
        ('skipped', 'Pominięto'),
    ]
    
    website = models.ForeignKey(NewsWebsite, on_delete=models.CASCADE, verbose_name="Serwis")
    crawl_session = models.ForeignKey(CrawlSession, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Sesja")
    
    url = models.URLField(max_length=1000, unique=True, verbose_name="URL artykułu")
    title = models.CharField(max_length=500, verbose_name="Tytuł artykułu")
    
    original_content = models.TextField(verbose_name="Oryginalna treść artykułu (HTML)")
    plain_text_content = models.TextField(verbose_name="Treść artykułu (plain text)")
    
    published_date_normalized = models.DateTimeField(verbose_name="Data publikacji (dd.mm.yyyy HH:mm:ss)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success', verbose_name="Status")
    http_status_code = models.PositiveIntegerField(null=True, blank=True, verbose_name="Kod odpowiedzi HTTP")
    response_time = models.FloatField(null=True, blank=True, verbose_name="Czas odpowiedzi (s)")
    content_length = models.PositiveIntegerField(null=True, blank=True, verbose_name="Długość zawartości")
    
    error_message = models.TextField(blank=True, verbose_name="Komunikat błędu")
    
    scraped_at = models.DateTimeField(auto_now_add=True, verbose_name="Scrapowano")
    
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadane")
    
    class Meta:
        verbose_name = "Artykuł"
        verbose_name_plural = "Artykuły"
        ordering = ['-published_date_normalized']
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['status']),
            models.Index(fields=['published_date_normalized']),
            models.Index(fields=['scraped_at']),
            models.Index(fields=['website']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.website.name}"
    
    def get_published_date_formatted(self):
        return self.published_date_normalized.strftime('%d.%m.%Y %H:%M:%S')
    
    def get_word_count(self):
        if self.plain_text_content:
            return len(self.plain_text_content.split())
        return 0
    
    def has_content(self):
        return bool(self.plain_text_content.strip())
    
    def get_excerpt(self, length=200):
        if self.plain_text_content:
            return self.plain_text_content[:length] + "..." if len(self.plain_text_content) > length else self.plain_text_content
        return ""

class ArticleTag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nazwa tagu")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Opis")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    
    class Meta:
        verbose_name = "Tag artykułu"
        verbose_name_plural = "Tagi artykułów"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ArticleTagRelation(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Artykuł")
    tag = models.ForeignKey(ArticleTag, on_delete=models.CASCADE, verbose_name="Tag")
    
    class Meta:
        verbose_name = "Relacja artykuł-tag"
        verbose_name_plural = "Relacje artykuł-tag"
        unique_together = ['article', 'tag']
    
    def __str__(self):
        return f"{self.article.title} - {self.tag.name}"