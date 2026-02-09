from django.urls import path
from . import views

app_name = 'member'

urlpatterns = [
    path('info/', views.info, name='info'),
    path('edit/', views.edit, name='edit'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('password/', views.edit_password, name='password'),
    path('myreservation/', views.myreservation, name='myreservation'),
    path('myrecruitment/', views.myrecruitment, name='myrecruitment'),
    path('myarticle/', views.myarticle, name='myarticle'),
    path('myjoin/', views.myjoin, name='myjoin'),
    path('myreservation/<str:reservation_num>', views.myreservation_detail, name='myreservation_detail'),
    path("cancel/<str:reservation_num>/", views.reservation_cancel, name="reservation_cancel"),
    path("cancel-timeslot/<reservation_num>/", views.cancel_timeslot, name="cancel_timeslot"),


    # 삭제 API
    path('api/article/delete/', views.delete_my_article, name='delete_my_article'),
    path('api/community/delete/', views.delete_my_community, name='delete_my_community'),
    path('clear-rejoin-message/', views.clear_rejoin_message, name='clear_rejoin_message'),

    

]