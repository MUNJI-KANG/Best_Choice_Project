from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('login/kakao/', views.kakao_login, name='kakao_login'),
    path('login/kakao/callback/', views.kakao_callback, name='kakao_callback'),
    path('signup/', views.signup, name='signup'),
    path('findID/', views.find_id, name='findID'),
    path('findPW/', views.find_pw, name='findPW'),
    path('terms/', views.terms, name = 'terms'),

    # 회원가입 검증
    path('check/userid/', views.check_userid, name='check_userid'),
    path('check/nickname/', views.check_nickname, name='check_nickname'),
    path('check/phone/', views.check_phone, name='check_phone'),

    # 로그아웃
    path("logout/", views.logout, name="logout"),

    # 공통 API
    path("api/weather/", views.weather_api, name="weather_api"),
]