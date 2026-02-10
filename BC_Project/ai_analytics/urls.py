from django.urls import path
from . import views

app_name = 'ai_analytics'

urlpatterns = [
    path('dashboard/', views.ai_analytics_dashboard, name='dashboard'),
    path('analyze/', views.ai_analyze_ajax, name='analyze_ajax'),
    path('chat/', views.ai_chat_ajax, name='chat_ajax'),
    path('chat/clear/', views.ai_chat_clear, name='chat_clear'),
    path('chat/export/', views.ai_chat_export, name='chat_export'),
]

