from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('api/articles/', views.articles_list_api, name='articles_list_api'),
    path('api/articles/<int:article_id>/', views.article_detail_api, name='article_detail_api'),
    path('api/websites/', views.websites_list_api, name='websites_list_api'),
    path('api/scrape/', views.scrape_articles_api, name='scrape_articles_api'),
    path('api/export/csv/', views.export_articles_csv_api, name='export_csv_api'),
    path('api/export/json/', views.export_articles_json_api, name='export_json_api'),
    
    path('articles/', views.articles_list, name='articles_list'),
    path('articles/<int:article_id>/', views.article_detail, name='article_detail'),
]