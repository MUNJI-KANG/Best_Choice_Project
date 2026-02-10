from django.urls import path
from . import views

app_name = 'board'

urlpatterns = [
    path('', views.article_list, name='board'),  # 기본 경로는 공지사항으로
    # path('faq/', views.faq, name='faq'),

    path('<str:board_name>/', views.article_list, name='list'),
    path('<str:board_name>/write/', views.article_write, name='write'),
    path('<str:board_name>/write/<int:article_id>', views.article_write, name='update'),
    path('<str:board_name>/<int:article_id>/', views.article_detail, name = 'detail'),
    
    path('<str:board_name>/<int:article_id>/comment/', views.article_comment, name='comment'),
    
    # 첨부파일
    path('download/file/<int:file_id>/', views.facility_file_download, name='download'),
    # 관리자 댓글 삭제 API
    path('api/comment/delete/', views.delete_comment, name='delete_comment'),
]