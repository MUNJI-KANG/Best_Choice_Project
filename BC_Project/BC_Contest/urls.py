"""
URL configuration for BC_Contest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    #path('', views.index),
    # path('login/', views.login),
    # path('signup/', views.signup),
    path('board/', include("board.urls")), 
    path('member/', include("member.urls")), 
    path('recruitment/', include("recruitment.urls")), 
    path('reservation/', include("reservation.urls")), 
    path('', include("common.urls")), 
    path('facility/', include("facility.urls")),
    path('manager/', include('manager.urls')),
    path('ai-analytics/', include('ai_analytics.urls')),
]

# Media files serving (개발 환경에서만)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)