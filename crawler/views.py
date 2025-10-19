from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core import serializers
import json
import csv

from .models import NewsWebsite, Article, CrawlSession
from .scraper import scrape_articles

def home(request):
    total_articles = Article.objects.count()
    total_websites = NewsWebsite.objects.count()
    total_sessions = CrawlSession.objects.count()
    
    recent_articles = Article.objects.select_related('website').order_by('-scraped_at')[:10]
    
    recent_sessions = CrawlSession.objects.select_related('website').order_by('-created_at')[:5]
    
    context = {
        'total_articles': total_articles,
        'total_websites': total_websites,
        'total_sessions': total_sessions,
        'recent_articles': recent_articles,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'crawler/home.html', context)

def articles_list_api(request):
    try:
        source = request.GET.get('source', '')
        
        articles = Article.objects.select_related('website').order_by('-published_date_normalized')
        
        if source:
            articles = articles.filter(website__domain__icontains=source)
        
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        paginator = Paginator(articles, per_page)
        page_obj = paginator.get_page(page)
        
        articles_data = []
        for article in page_obj:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'url': article.url,
                'source_domain': article.website.domain,
                'published_date': article.get_published_date_formatted(),
                'scraped_at': article.scraped_at.strftime('%d.%m.%Y %H:%M:%S'),
                'status': article.status,
                'word_count': article.get_word_count(),
                'excerpt': article.get_excerpt(200)
            })
        
        return JsonResponse({
            'status': 'success',
            'total': paginator.count,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'articles': articles_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def article_detail_api(request, article_id):
    try:
        article = get_object_or_404(Article, id=article_id)
        
        article_data = {
            'id': article.id,
            'title': article.title,
            'url': article.url,
            'source_domain': article.website.domain,
            'published_date': article.get_published_date_formatted(),
            'scraped_at': article.scraped_at.strftime('%d.%m.%Y %H:%M:%S'),
            'status': article.status,
            'word_count': article.get_word_count(),
            'original_content': article.original_content,
            'plain_text_content': article.plain_text_content,
            'http_status_code': article.http_status_code,
            'response_time': article.response_time,
            'content_length': article.content_length,
            'error_message': article.error_message if article.error_message else None
        }
        
        return JsonResponse({
            'status': 'success',
            'article': article_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def websites_list_api(request):
    try:
        websites = NewsWebsite.objects.all().order_by('-created_at')
        
        websites_data = []
        for website in websites:
            websites_data.append({
                'id': website.id,
                'name': website.name,
                'url': website.url,
                'domain': website.domain,
                'description': website.description,
                'is_active': website.is_active,
                'created_at': website.created_at.strftime('%d.%m.%Y %H:%M:%S'),
                'articles_count': website.article_set.count()
            })
        
        return JsonResponse({
            'status': 'success',
            'websites': websites_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def scrape_articles_api(request):
    try:
        results = scrape_articles()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Scrapowanie zakończone',
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def export_articles_csv_api(request):
    try:
        articles = Article.objects.select_related('website').order_by('-published_date_normalized')
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="articles.csv"'
        
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        writer.writerow([
            'ID', 'Tytuł', 'URL', 'Domena', 'Data publikacji', 
            'Data scrapowania', 'Status', 'Liczba słów', 'Treść (plain text)'
        ])
        
        for article in articles:
            writer.writerow([
                article.id,
                article.title,
                article.url,
                article.website.domain,
                article.get_published_date_formatted(),
                article.scraped_at.strftime('%d.%m.%Y %H:%M:%S'),
                article.get_status_display(),
                article.get_word_count(),
                article.plain_text_content
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def export_articles_json_api(request):
    try:
        articles = Article.objects.select_related('website').order_by('-published_date_normalized')
        
        articles_data = []
        for article in articles:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'url': article.url,
                'source_domain': article.website.domain,
                'published_date': article.get_published_date_formatted(),
                'scraped_at': article.scraped_at.strftime('%d.%m.%Y %H:%M:%S'),
                'status': article.status,
                'word_count': article.get_word_count(),
                'original_content': article.original_content,
                'plain_text_content': article.plain_text_content
            })
        
        response = HttpResponse(
            json.dumps(articles_data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="articles.json"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def articles_list(request):
    articles = Article.objects.select_related('website').order_by('-published_date_normalized')
    
    search_query = request.GET.get('search', '')
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) | 
            Q(plain_text_content__icontains=search_query)
        )
    
    paginator = Paginator(articles, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'crawler/articles_list.html', context)

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    context = {
        'article': article,
    }
    
    return render(request, 'crawler/article_detail.html', context)