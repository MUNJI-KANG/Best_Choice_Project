
from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import Count,Sum
from django.db import connection
from django.utils import timezone
from datetime import timedelta

import json
import pandas as pd

from django_pandas.io import read_frame
from django.contrib import messages


from common.utils import is_manager

# models import 
from member.models import Member
from recruitment.models import Community, EndStatus, JoinStat
from reservation.models import Reservation
from board.models import Article
from common.models import Comment
from common.paging import pager
from facility.models import Facility



def dashboard(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    """
    관리자 대시보드
    DB가 없어도 동작하도록 모든 DB 쿼리에 예외 처리 포함
    """
    # 필터 파라미터
    region_filter = request.GET.get('region', '')
    sport_filter = request.GET.get('sport', '')
    date_range = request.GET.get('date_range', '7')  # 기본 7일
    
    try:
        days = int(date_range)
    except (ValueError, TypeError):
        days = 7
    
    start_date = timezone.now() - timedelta(days=days)
    
    # ============================================
    # 1. 실시간 현황 KPI 카드
    # ============================================
    today = timezone.now().date()
    
    kpi_data = {
        'today_reservations': 0,
        'today_communities': 0,
        'today_members': 0,
        'active_communities': 0,
    }
    
    try:
        # DB 연결 확인
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # DB가 있으면 쿼리 실행
        try:
            kpi_data = {
                'today_reservations': Reservation.objects.filter(
                    reg_date__date=today,
                    delete_yn=0
                ).count(),
                'today_communities': Community.objects.filter(
                    reg_date__date=today,
                    delete_date__isnull=True
                ).count(),
                'today_members': Member.objects.filter(
                    reg_date__date=today,
                    delete_yn=0
                ).count(),
                'active_communities': Community.objects.filter(
                    delete_date__isnull=True
                ).count(),
            }
        except Exception as e:
            # 테이블이 없거나 쿼리 실패 시 기본값 유지
            pass
    except Exception:
        # DB 연결 자체가 안되면 기본값 유지
        pass
    
    # ============================================
    # 2. 예약/모집글 통계 (일별 추이)
    # ============================================
    daily_recruitment = {}
    daily_reservations = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            communities = Community.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            )
            
            if region_filter:
                communities = communities.filter(region=region_filter)
            if sport_filter:
                communities = communities.filter(sport_type=sport_filter)
            
            # pandas로 일별 집계
            if communities.exists():
                df_communities = read_frame(communities.values('reg_date', 'region', 'sport_type'))
                if not df_communities.empty:
                    df_communities['date'] = pd.to_datetime(df_communities['reg_date']).dt.date
                    daily_recruitment = df_communities.groupby('date').size().to_dict()
                    # 날짜를 문자열로 변환 (JSON 직렬화)
                    daily_recruitment = {str(k): int(v) for k, v in daily_recruitment.items()}
            
            # 예약 추이
            reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            )
            
            if reservations.exists():
                df_reservations = read_frame(reservations.values('reg_date'))
                if not df_reservations.empty:
                    df_reservations['date'] = pd.to_datetime(df_reservations['reg_date']).dt.date
                    daily_reservations = df_reservations.groupby('date').size().to_dict()
                    daily_reservations = {str(k): int(v) for k, v in daily_reservations.items()}
        except Exception:
            # 테이블이 없거나 쿼리 실패 시 빈 딕셔너리 유지
            pass
    except Exception:
        # DB 연결 실패 시 빈 딕셔너리 유지
        pass
    
    # ============================================
    # 3. 모집 완료 추이
    # ============================================
    completion_trend = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            end_statuses = EndStatus.objects.select_related('community').filter(
                community__reg_date__gte=start_date
            )
            
            if region_filter:
                end_statuses = end_statuses.filter(community__region=region_filter)
            if sport_filter:
                end_statuses = end_statuses.filter(community__sport_type=sport_filter)
            
            if end_statuses.exists():
                df_end = read_frame(end_statuses.values('community__reg_date', 'end_stat'))
                if not df_end.empty:
                    df_end['date'] = pd.to_datetime(df_end['community__reg_date']).dt.date
                    total_by_date = df_end.groupby('date').size()
                    completed_by_date = df_end[df_end['end_stat'] == 1].groupby('date').size()
                    
                    for date in total_by_date.index:
                        total = int(total_by_date.get(date, 0))
                        completed = int(completed_by_date.get(date, 0))
                        completion_trend[str(date)] = {
                            'total': total,
                            'completed': completed,
                            'rate': round((completed / total * 100) if total > 0 else 0, 1)
                        }
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 4. 게시판 통계
    # ============================================
    board_stats = []
    comment_count = 0
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            articles = Article.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            )
            
            board_stats = list(articles.values('board_id__board_name').annotate(
                count=Count('article_id'),
                total_views=Sum('view_cnt')
            ))
            
            # 댓글 통계
            comment_count = Comment.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            ).count()
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 5. 회원 가입 추이
    # ============================================
    daily_members = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            members = Member.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            )
            
            if members.exists():
                df_members = read_frame(members.values('reg_date'))
                if not df_members.empty:
                    df_members['date'] = pd.to_datetime(df_members['reg_date']).dt.date
                    daily_members = df_members.groupby('date').size().to_dict()
                    daily_members = {str(k): int(v) for k, v in daily_members.items()}
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 6. 성별 분포
    # ============================================
    gender_data = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            gender_dist = Member.objects.filter(delete_yn=0).values('gender').annotate(
                count=Count('member_id')
            )
            gender_data = {str(item['gender']): item['count'] for item in gender_dist}
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 7. 예약 취소율 (개선: 기간별 추이 포함)
    # ============================================
    cancellation_rate = 0
    daily_cancellation_rate = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            # 전체 취소율
            total_reservations = Reservation.objects.filter(reg_date__gte=start_date).count()
            cancelled_reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=1
            ).count()
            
            cancellation_rate = round((cancelled_reservations / total_reservations * 100) if total_reservations > 0 else 0, 2)
            
            # 일별 취소율 추이
            all_reservations = Reservation.objects.filter(reg_date__gte=start_date)
            if all_reservations.exists():
                df_all = read_frame(all_reservations.values('reg_date', 'delete_yn'))
                if not df_all.empty:
                    df_all['date'] = pd.to_datetime(df_all['reg_date']).dt.date
                    df_all['is_cancelled'] = df_all['delete_yn'] == 1
                    
                    # 일별 총 예약 수
                    daily_total = df_all.groupby('date').size()
                    # 일별 취소 수
                    daily_cancelled = df_all[df_all['is_cancelled']].groupby('date').size()
                    
                    for date in daily_total.index:
                        total = int(daily_total.get(date, 0))
                        cancelled = int(daily_cancelled.get(date, 0))
                        rate = round((cancelled / total * 100) if total > 0 else 0, 2)
                        daily_cancellation_rate[str(date)] = {
                            'total': total,
                            'cancelled': cancelled,
                            'rate': rate
                        }
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 8. 참여율 통계 (개선: 기간별 추이 포함)
    # ============================================
    participation_rate = 0
    daily_participation_rate = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            join_stats = JoinStat.objects.select_related('community_id').filter(
                community_id__reg_date__gte=start_date
            )
            
            if region_filter:
                join_stats = join_stats.filter(community_id__region=region_filter)
            if sport_filter:
                join_stats = join_stats.filter(community_id__sport_type=sport_filter)
            
            if join_stats.exists():
                df_join = read_frame(join_stats.values('community_id__reg_date', 'join_status'))
                if not df_join.empty:
                    # 전체 참여율
                    total_joins = len(df_join)
                    completed_joins = len(df_join[df_join['join_status'] == 1])
                    participation_rate = round((completed_joins / total_joins * 100) if total_joins > 0 else 0, 2)
                    
                    # 일별 참여율 추이
                    df_join['date'] = pd.to_datetime(df_join['community_id__reg_date']).dt.date
                    df_join['is_completed'] = df_join['join_status'] == 1
                    
                    daily_total_joins = df_join.groupby('date').size()
                    daily_completed_joins = df_join[df_join['is_completed']].groupby('date').size()
                    
                    for date in daily_total_joins.index:
                        total = int(daily_total_joins.get(date, 0))
                        completed = int(daily_completed_joins.get(date, 0))
                        rate = round((completed / total * 100) if total > 0 else 0, 2)
                        daily_participation_rate[str(date)] = {
                            'total': total,
                            'completed': completed,
                            'rate': rate
                        }
        except Exception:
            pass
    except Exception:
        pass
    
    # ============================================
    # 9. 성별 분포 (개선: 예약자/참여자 기준 추가)
    # ============================================
    gender_data = {}  # 전체 회원
    reservation_gender_data = {}  # 예약자 성별
    participation_gender_data = {}  # 참여자 성별
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            # 전체 회원 성별 분포
            gender_dist = Member.objects.filter(delete_yn=0).values('gender').annotate(
                count=Count('member_id')
            )
            gender_data = {str(item['gender']): item['count'] for item in gender_dist}
            
            # 예약자 성별 분포
            reservations_with_member = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            ).select_related('member')
            
            if reservations_with_member.exists():
                reservation_gender_dist = reservations_with_member.values('member__gender').annotate(
                    count=Count('reservation_id')
                )
                reservation_gender_data = {str(item['member__gender']): item['count'] for item in reservation_gender_dist}
            
            # 참여자 성별 분포 (join_status=1인 경우만)
            join_stats_with_member = JoinStat.objects.select_related('member_id', 'community_id').filter(
                community_id__reg_date__gte=start_date,
                join_status=1
            )
            
            if region_filter:
                join_stats_with_member = join_stats_with_member.filter(community_id__region=region_filter)
            if sport_filter:
                join_stats_with_member = join_stats_with_member.filter(community_id__sport_type=sport_filter)
            
            if join_stats_with_member.exists():
                participation_gender_dist = join_stats_with_member.values('member_id__gender').annotate(
                    count=Count('member_id')
                )
                participation_gender_data = {str(item['member_id__gender']): item['count'] for item in participation_gender_dist}
        except Exception:
            pass
    except Exception:
        pass
    
    # 지역별, 종목별 옵션
    regions = []
    sports = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            regions = list(Community.objects.values_list('region', flat=True).distinct())
            sports = list(Community.objects.values_list('sport_type', flat=True).distinct())
        except Exception:
            pass
    except Exception:
        pass
    
    context = {
        'kpi_data': kpi_data,
        'daily_recruitment': json.dumps(daily_recruitment),
        'daily_reservations': json.dumps(daily_reservations),
        'completion_trend': json.dumps(completion_trend),
        'board_stats': board_stats,
        'comment_count': comment_count,
        'daily_members': json.dumps(daily_members),
        'gender_data': json.dumps(gender_data),
        'reservation_gender_data': json.dumps(reservation_gender_data),
        'participation_gender_data': json.dumps(participation_gender_data),
        'cancellation_rate': cancellation_rate,
        'daily_cancellation_rate': json.dumps(daily_cancellation_rate),
        'participation_rate': participation_rate,
        'daily_participation_rate': json.dumps(daily_participation_rate),
        'regions': regions,
        'sports': sports,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
        'date_range': date_range,
    }
    
    return render(request, 'manager/dashboard.html', context)


def facility_inspection_stats(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    """
    시설 안전점검 통계 페이지
    """
    # 필터 파라미터
    region_filter = request.GET.get('region', '')
    sport_filter = request.GET.get('sport', '')
    
    # 연도별 점검 추세
    yearly_inspection_trend = {}
    # 등급별 분포
    grade_distribution = {}
    # 지역별 안전점검 통계
    region_inspection_stats = {}
    # 종목별 안전점검 통계
    sport_inspection_stats = {}
    
    # 지역/종목 옵션
    regions = []
    sports = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            
            # 필터 적용
            if region_filter:
                facilities = facilities.filter(cp_nm=region_filter)
            if sport_filter:
                facilities = facilities.filter(fcob_nm=sport_filter)
            
            if facilities.exists():
                df_facilities = read_frame(facilities.values(
                    'schk_visit_ymd', 'schk_tot_grd_nm', 'cp_nm', 'fcob_nm'
                ))
                
                if not df_facilities.empty:
                    # 연도별 점검 추세 (2000~현재년도)
                    current_year = timezone.now().year
                    df_facilities['year'] = df_facilities['schk_visit_ymd'].str[:4]
                    df_facilities['year_int'] = pd.to_numeric(df_facilities['year'], errors='coerce')
                    valid_df = df_facilities[(df_facilities['year_int'] >= 2000) & (df_facilities['year_int'] <= current_year)]
                    yearly_trend = valid_df.groupby('year').size()
                    
                    # 최초 년도와 최종 년도 확인
                    min_year = int(valid_df['year'].min()) if not valid_df['year'].empty else 2020
                    max_year = current_year  # 올해
                    
                    # 모든 년도에 대해 데이터 채우기 (없으면 0)
                    yearly_inspection_trend = {}
                    for year in range(min_year, max_year + 1):
                        year_str = str(year)
                        yearly_inspection_trend[year_str] = int(yearly_trend.get(year_str, 0))
                    
                    # 등급별 분포
                    grade_dist = df_facilities['schk_tot_grd_nm'].value_counts()
                    grade_distribution = {str(k): int(v) for k, v in grade_dist.items() if pd.notna(k)}
                    
                    # 지역별 안전점검 통계
                    if 'cp_nm' in df_facilities.columns:
                        for region in df_facilities['cp_nm'].dropna().unique():
                            region_df = df_facilities[df_facilities['cp_nm'] == region]
                            grade_counts = region_df['schk_tot_grd_nm'].value_counts()
                            region_inspection_stats[str(region)] = {
                                str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)
                            }
                    
                    # 종목별 안전점검 통계
                    if 'fcob_nm' in df_facilities.columns:
                        for sport in df_facilities['fcob_nm'].dropna().unique():
                            sport_df = df_facilities[df_facilities['fcob_nm'] == sport]
                            grade_counts = sport_df['schk_tot_grd_nm'].value_counts()
                            sport_inspection_stats[str(sport)] = {
                                str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)
                            }
            
            # 필터 옵션 가져오기
            all_facilities = Facility.objects.exclude(cp_nm__isnull=True).exclude(cp_nm='')
            regions = list(all_facilities.values_list('cp_nm', flat=True).distinct())
            
            all_facilities_sport = Facility.objects.exclude(fcob_nm__isnull=True).exclude(fcob_nm='')
            sports = list(all_facilities_sport.values_list('fcob_nm', flat=True).distinct())
            
        except Exception as e:
            print(f"[시설 안전점검 통계] 오류: {e}")
            pass
    except Exception:
        pass
    
    context = {
        'yearly_inspection_trend': json.dumps(yearly_inspection_trend),
        'grade_distribution': json.dumps(grade_distribution),
        'region_inspection_stats': json.dumps(region_inspection_stats),
        'sport_inspection_stats': json.dumps(sport_inspection_stats),
        'regions': regions,
        'sports': sports,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
    }
    
    return render(request, 'manager/facility_inspection_stats.html', context)


def facility_inspection_yearly_detail(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    """
    연도별 안전점검 추세 상세 페이지
    연도, 지역, 종목을 교차 선택하여 통계 확인 가능
    """
    # 필터 파라미터 (모두 동시 선택 가능)
    year_filter = request.GET.get('year', '')  # 단일 선택
    region_filter = request.GET.get('region', '')
    sport_filter = request.GET.get('sport', '')
    
    # 통계 데이터
    stats_data = {}
    grade_by_year = {}  # 연도별 등급별 분포
    summary_stats = {
        'total_inspections': 0,
        'avg_per_year': 0,
        'max_year': '',
        'min_year': ''
    }
    
    # 옵션 리스트
    years = []
    regions = []
    sports = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            
            # 필터 적용 (모두 동시 적용)
            if year_filter:
                facilities = facilities.filter(schk_visit_ymd__startswith=year_filter)
            if region_filter:
                facilities = facilities.filter(cp_nm=region_filter)
            if sport_filter:
                facilities = facilities.filter(fcob_nm=sport_filter)
            
            if facilities.exists():
                df_facilities = read_frame(facilities.values(
                    'schk_visit_ymd', 'schk_tot_grd_nm', 'cp_nm', 'fcob_nm'
                ))
                
                if not df_facilities.empty:
                    df_facilities['year'] = df_facilities['schk_visit_ymd'].str[:4]
                    
                    # 연도별 통계 (2000~현재년도)
                    current_year = timezone.now().year
                    df_facilities['year_int'] = pd.to_numeric(df_facilities['year'], errors='coerce')
                    valid_df = df_facilities[(df_facilities['year_int'] >= 2000) & (df_facilities['year_int'] <= current_year)]
                    
                    # 전체 연도 표시 (선택된 연도 필터는 이미 적용됨)
                    yearly_trend = valid_df.groupby('year').size()
                    min_year = int(valid_df['year'].min()) if not valid_df['year'].empty else 2020
                    max_year = current_year
                    
                    # 연도별 점검 건수
                    for year in range(min_year, max_year + 1):
                        year_str = str(year)
                        stats_data[year_str] = int(yearly_trend.get(year_str, 0))
                    
                    # 연도별 등급별 분포 (상세 정보용)
                    grade_by_year = {}
                    if 'schk_tot_grd_nm' in valid_df.columns:
                        for year in range(min_year, max_year + 1):
                            year_str = str(year)
                            year_df = valid_df[valid_df['year'] == year_str]
                            if not year_df.empty:
                                grade_counts = year_df['schk_tot_grd_nm'].value_counts()
                                grade_by_year[year_str] = {
                                    str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)
                                }
                            else:
                                grade_by_year[year_str] = {}
                    
                    # 요약 통계
                    summary_stats['total_inspections'] = len(df_facilities)
                    if stats_data:
                        non_zero_years = {k: v for k, v in stats_data.items() if v > 0}
                        if non_zero_years:
                            summary_stats['avg_per_year'] = round(sum(non_zero_years.values()) / len(non_zero_years), 1)
                            summary_stats['max_year'] = max(non_zero_years, key=non_zero_years.get)
                            summary_stats['min_year'] = min(non_zero_years, key=non_zero_years.get)
            
            # 옵션 리스트 생성 (2000~현재년도)
            current_year = timezone.now().year
            all_facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            if all_facilities.exists():
                df_all = read_frame(all_facilities.values('schk_visit_ymd'))
                if not df_all.empty:
                    df_all['year'] = df_all['schk_visit_ymd'].str[:4]
                    # 연도 유효성 검사 (2000~현재년도)
                    df_all['year_int'] = pd.to_numeric(df_all['year'], errors='coerce')
                    valid_years = df_all[(df_all['year_int'] >= 2000) & (df_all['year_int'] <= current_year)]['year'].unique()
                    years = sorted(valid_years.tolist(), reverse=True)
            
            all_regions = Facility.objects.exclude(cp_nm__isnull=True).exclude(cp_nm='')
            regions = list(all_regions.values_list('cp_nm', flat=True).distinct())
            
            all_sports = Facility.objects.exclude(fcob_nm__isnull=True).exclude(fcob_nm='')
            sports = list(all_sports.values_list('fcob_nm', flat=True).distinct())
            
        except Exception as e:
            print(f"[연도별 상세] 오류: {e}")
            pass
    except Exception:
        pass
    
    context = {
        'stats_data': json.dumps(stats_data),
        'grade_by_year': json.dumps(grade_by_year),
        'summary_stats': summary_stats,
        'years': years,
        'regions': regions,
        'sports': sports,
        'selected_year': year_filter,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
    }
    
    return render(request, 'manager/facility_inspection_yearly_detail.html', context)


def facility_inspection_grade_detail(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    """
    등급별 분포 상세 페이지 (시설 목록 표시)
    """
    # 필터 파라미터
    year_filter = request.GET.get('year', '')
    region_filter = request.GET.get('region', '')
    sport_filter = request.GET.get('sport', '')
    grade_filter = request.GET.get('grade', '')  # 양호, 주의, 경고, 사용중지
    
    # 페이징 파라미터
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    # 옵션 리스트
    years = []
    regions = []
    sports = []
    grades = ['양호', '주의', '경고']
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        try:
            facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            
            # 연도 필터링 (2000~현재년도)
            current_year = timezone.now().year
            facilities = facilities.extra(
                where=[f"SUBSTRING(schk_visit_ymd, 1, 4) >= '2000' AND SUBSTRING(schk_visit_ymd, 1, 4) <= '{current_year}'"]
            )
            
            # 필터 적용
            if year_filter:
                facilities = facilities.filter(schk_visit_ymd__startswith=year_filter)
            if region_filter:
                facilities = facilities.filter(cp_nm=region_filter)
            if sport_filter:
                facilities = facilities.filter(fcob_nm=sport_filter)
            if grade_filter:
                facilities = facilities.filter(schk_tot_grd_nm=grade_filter)
            
            paging = pager(request, facilities, per_page=per_page)
            
            
            # 시설 목록 생성 (values()로 성능 개선)
            start_index = (paging['page_obj'].number - 1) * per_page
            facilities_list = []
            
            for idx, fac in enumerate(paging['page_obj'].object_list):
                # 점검일자 포맷팅
                visit_date = fac.schk_visit_ymd
                if visit_date and len(visit_date) == 8:
                    visit_date_formatted = f"{visit_date[:4]}-{visit_date[4:6]}-{visit_date[6:8]}"
                else:
                    visit_date_formatted = visit_date or '-'
                
                facilities_list.append({
                    'faci_cd': fac.faci_cd,
                    'faci_nm': fac.faci_nm or '-',
                    'cp_nm': fac.cp_nm or '-',
                    'fcob_nm': fac.fcob_nm or '-',
                    'faci_road_addr': fac.faci_road_addr or fac.faci_addr or '-',
                    'schk_visit_ymd': visit_date_formatted,
                    'schk_tot_grd_nm': fac.schk_tot_grd_nm or '-',
                    'faci_stat_nm': fac.faci_stat_nm or '-',  # 시설 상태 (사유로 활용)
                    'faci_tel_no': fac.faci_tel_no or '-',
                    'row_no': start_index + idx + 1,
                })
            
            # 옵션 리스트 생성 (2000~현재년도)
            current_year = timezone.now().year
            all_facilities = Facility.objects.exclude(schk_visit_ymd__isnull=True).exclude(schk_visit_ymd='')
            if all_facilities.exists():
                df_all = read_frame(all_facilities.values('schk_visit_ymd'))
                if not df_all.empty:
                    df_all['year'] = df_all['schk_visit_ymd'].str[:4]
                    # 연도 유효성 검사 (2000~현재년도)
                    df_all['year_int'] = pd.to_numeric(df_all['year'], errors='coerce')
                    valid_years = df_all[(df_all['year_int'] >= 2000) & (df_all['year_int'] <= current_year)]['year'].unique()
                    years = sorted(valid_years.tolist(), reverse=True)
            
            all_regions = Facility.objects.exclude(cp_nm__isnull=True).exclude(cp_nm='')
            regions = list(all_regions.values_list('cp_nm', flat=True).distinct())
            
            all_sports = Facility.objects.exclude(fcob_nm__isnull=True).exclude(fcob_nm='')
            sports = list(all_sports.values_list('fcob_nm', flat=True).distinct())
            
        except Exception as e:
            print(f"[등급별 상세] 오류: {e}")
            pass
    except Exception:
        pass
    
    context = {
        'facilities_list': facilities_list,
        'page_obj': paging['page_obj'],
        'paginator': paging['paginator'],
        'per_page': per_page,
        'block_range': paging['block_range'],
        'years': years,
        'regions': regions,
        'sports': sports,
        'grades': grades,
        'selected_year': year_filter,
        'selected_region': region_filter,
        'selected_sport': sport_filter,
        'selected_grade': grade_filter,
    }
    
    return render(request, 'manager/facility_inspection_grade_detail.html', context)