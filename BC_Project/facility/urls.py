from django.urls import path
from . import views

app_name = 'facility'

urlpatterns = [
    path('', views.facility_list, name='list'),
    path('detail/<fk>/', views.facility_detail, name='detail'),
    path('comment/<fk>/', views.add_comment, name="facility_comment"),
    
]
