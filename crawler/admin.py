from django.contrib import admin
from .models import NewsWebsite, Article, CrawlSession, ArticleTag, ArticleTagRelation

@admin.register(NewsWebsite)
class NewsWebsiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'url', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'domain', 'url']
    readonly_fields = ['created_at']

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'website', 'published_date_normalized', 'status', 'scraped_at', 'get_word_count']
    list_filter = ['status', 'website', 'scraped_at', 'published_date_normalized']
    search_fields = ['title', 'plain_text_content', 'url']
    readonly_fields = ['scraped_at', 'response_time', 'content_length']
    date_hierarchy = 'scraped_at'
    
    def get_word_count(self, obj):
        return obj.get_word_count()
    get_word_count.short_description = 'Liczba słów'

@admin.register(CrawlSession)
class CrawlSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'status', 'started_at', 'completed_at', 'get_progress']
    list_filter = ['status', 'website', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    def get_progress(self, obj):
        if obj.total_urls > 0:
            return f"{obj.scraped_urls}/{obj.total_urls} ({obj.get_progress_percentage():.1f}%)"
        return "0/0"
    get_progress.short_description = 'Postęp'

@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ArticleTagRelation)
class ArticleTagRelationAdmin(admin.ModelAdmin):
    list_display = ['article', 'tag']
    list_filter = ['tag']
    search_fields = ['article__title', 'tag__name']
