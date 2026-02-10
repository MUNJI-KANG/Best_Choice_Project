from django.urls import path
from . import views

app_name = 'reservation'

urlpatterns = [
    path('', views.reservation_list, name='reservation_list'),    
    path('<str:facility_id>', views.reservation_detail, name='reservation_detail'),
    path("save/", views.reservation_save, name="reservation_save"),
]