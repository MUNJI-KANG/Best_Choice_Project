from django.urls import path
from . import views, facility_manager, recruitment_manager, board, inspection, member

app_name = 'manager'

urlpatterns = [
    path('', views.manager, name='manager_login'),
    path("logout/", views.logout, name="logout"),
    path("edit/", views.info_edit, name="info_edit"),


    # 공공시설추가페이지
    path('facility_add/', facility_manager.facility, name='facility_add'),
      
    # 종목 관리
    path("add_sport/", facility_manager.add_sport, name="add_sport"),
    path("save_selected_sports/", facility_manager.save_selected_sports, name="save_selected_sports"),
    path('sport_delete/', facility_manager.sport_delete, name='sport_delete'),

    # 시설등록
    path("facility_register/", facility_manager.facility_register, name="facility_register"),
    
    # 시설관리
    path('facility_list/', facility_manager.facility_list, name='facility_list'),
    path('facility/<id>/', facility_manager.facility_detail, name='facility_detail'),
    path('facility/<id>/modify/', facility_manager.facility_modify, name='facility_modify'),
    path('delete/', facility_manager.facility_delete, name='facility_delete'),

    # 시설 첨부파일 다운로드
    path('download/file/<int:file_id>/', facility_manager.facility_file_download, name='download'),
    # 예약현황
    path('reservations/', facility_manager.reservation_list_manager, name='reservation_list_manager'),



    # 모집글관리
    path('recruitment_manager/', recruitment_manager.recruitment_manager, name='recruitment_manager'),
    path('recruitment_manager/detail/<int:id>/', recruitment_manager.recruitment_detail, name='recruitment_detail'),
    path('recruitment/delete/', recruitment_manager.delete_recruitment, name='delete_recruitment'), # 삭제
    path('recruitment/harddelete/', recruitment_manager.hard_delete_recruitment, name='harddelete_recruitment'), # 영구삭제
    path('recruitment/restore/', recruitment_manager.restore_recruitment, name='restore_recruitment'), # 복구


    # 게시판 관리 + 배너 페이지
    path('board_list/<int:id>/',board.board_list, name='board_list'), # 목록
    path('board_write/<int:id>/',board.board_write, name='board_write'), # 작성
    path('board_write/<int:id>/<int:pk>/',board.board_write, name='board_edit'), # 수정
    path('board_detail/<int:pk>/',board.board_detail, name='board_detail'), # 상세페이지
    path('articles/delete/', board.delete_articles, name='delete_articles'), # 삭제 API
    path('articles/harddelete/', board.hard_delete_articles, name='harddelete_articles'),# 영구삭제
    path('articles/restore/', board.restore_articles, name='restore_articles'), # 복구

    path('banner/', board.banner_manager, name='banner_manager'),
    path('banner_form/', board.banner_form, name='banner_form'),
    path("banner_edit/<int:img_id>/", board.banner_edit, name="banner_edit"),
    path("banner_delete/", board.banner_delete, name="banner_delete"),
    path("banner_detail/<int:img_id>/", board.banner_detail, name="banner_detail"),
    path("banner_download/<int:img_id>/", board.banner_download, name="banner_download"),

    # 예약 취소 API
    path('api/reservations/cancel-timeslot/<str:reservation_num>/', facility_manager.manager_cancel_timeslot, name='manager_cancel_timeslot'),

    
    # 회원관리
    path('member_list/', member.member_list, name='member_list'),
    path("member/delete/", member.member_delete, name="member_delete"),
    path("member/restore/", member.member_restore, name="member_restore"),


    # 통계
    path('dashboard/', inspection.dashboard, name='dashboard'),
    path('facility_inspection_stats/', inspection.facility_inspection_stats, name='facility_inspection_stats'),
    path('facility_inspection_stats/yearly/', inspection.facility_inspection_yearly_detail, name='facility_inspection_yearly_detail'),
    path('facility_inspection_stats/grade/', inspection.facility_inspection_grade_detail, name='facility_inspection_grade_detail'),

]