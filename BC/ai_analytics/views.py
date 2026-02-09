from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.cache import cache
from datetime import timedelta
from django.db.models import Count, Sum, Avg
from django.db import connection
from django.contrib import messages
import json
import markdown
import bleach
import hashlib

from common.utils import is_manager
from ai_analytics.services import AIAnalyticsService
from member.models import Member
from reservation.models import Reservation
from recruitment.models import Community, JoinStat
from board.models import Article
from common.models import Comment
from facility.models import FacilityInfo, Facility


def analyze_question_needs(user_question):
    """
    사용자 질문을 분석해서 필요한 통계를 파악
    Returns: 필요한 통계 목록 (리스트)
    """
    question_lower = user_question.lower()
    needs = []
    
    # 성별 관련 통계
    if any(keyword in question_lower for keyword in ['성별', '남성', '여성', '남자', '여자']):
        if any(keyword in question_lower for keyword in ['취소', '취소율']):
            needs.append('gender_cancellation_rate')
        if any(keyword in question_lower for keyword in ['예약', '예약율']):
            needs.append('gender_reservation_rate')
        if any(keyword in question_lower for keyword in ['가입', '회원']):
            needs.append('gender_member_stats')
        if any(keyword in question_lower for keyword in ['참여', '참여율']):
            needs.append('gender_participation_rate')
    
    # 지역 관련 통계
    if any(keyword in question_lower for keyword in ['지역', '서울', '부산', '인천', '대구', '광주', '대전', '울산']):
        if any(keyword in question_lower for keyword in ['예약', '예약율']):
            needs.append('region_reservation_stats')
        if any(keyword in question_lower for keyword in ['모집', '모집글']):
            needs.append('region_community_stats')
        if any(keyword in question_lower for keyword in ['인기', '인기도']):
            needs.append('region_popularity')
    
    # 종목 관련 통계
    if any(keyword in question_lower for keyword in ['종목', '스포츠', '운동', '축구', '농구', '배구', '야구', '테니스']):
        if any(keyword in question_lower for keyword in ['예약', '예약율']):
            needs.append('sport_reservation_stats')
        if any(keyword in question_lower for keyword in ['모집', '모집글']):
            needs.append('sport_community_stats')
        if any(keyword in question_lower for keyword in ['인기', '인기도']):
            needs.append('sport_popularity')
        if any(keyword in question_lower for keyword in ['취소', '취소율']):
            needs.append('sport_cancellation_rate')
    
    # 시간대 관련 통계
    if any(keyword in question_lower for keyword in ['시간', '시간대', '오전', '오후', '저녁', '밤']):
        if any(keyword in question_lower for keyword in ['예약', '예약율']):
            needs.append('hourly_reservation_stats')
        if any(keyword in question_lower for keyword in ['취소', '취소율']):
            needs.append('hourly_cancellation_stats')
    
    # 요일 관련 통계
    if any(keyword in question_lower for keyword in ['요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일', '주말', '평일']):
        if any(keyword in question_lower for keyword in ['취소', '취소율']):
            needs.append('weekday_cancellation_rate')
        if any(keyword in question_lower for keyword in ['예약', '예약율']):
            needs.append('weekday_reservation_stats')
    
    # 시설 관련 통계
    if any(keyword in question_lower for keyword in ['시설', '체육관', '경기장']):
        if any(keyword in question_lower for keyword in ['인기', '인기도', '조회']):
            needs.append('facility_popularity')
        if any(keyword in question_lower for keyword in ['예약', '예약율']):
            needs.append('facility_reservation_stats')
    
    # 안전 통계 관련
    if any(keyword in question_lower for keyword in ['안전', '등급', '점검', '검사', 'safety', 'inspection', '안전등급', '안전점검']):
        needs.append('safety_overview')
        if any(keyword in question_lower for keyword in ['등급', 'grade', '레벨']):
            needs.append('safety_grade_stats')
        if any(keyword in question_lower for keyword in ['지역', 'region', '서울', '부산', '인천', '대구', '광주', '대전', '울산']):
            needs.append('safety_region_stats')
        if any(keyword in question_lower for keyword in ['종목', 'sport', '스포츠', '운동', '축구', '농구', '배구', '야구', '테니스']):
            needs.append('safety_sport_stats')
        if any(keyword in question_lower for keyword in ['연도', '년도', 'year', '트렌드', '추세']):
            needs.append('safety_yearly_trend')
        if any(keyword in question_lower for keyword in ['개선', '제안', '권장', '방안', '전략']):
            needs.append('safety_recommendations')
    
    return needs


def calculate_dynamic_stats(needs, start_date):
    """
    필요한 통계를 동적으로 계산
    """
    dynamic_stats = {}
    
    try:
        from django_pandas.io import read_frame
        import pandas as pd
        
        # 성별별 취소율
        if 'gender_cancellation_rate' in needs:
            reservations = Reservation.objects.filter(
                reg_date__gte=start_date
            ).select_related('member')
            
            if reservations.exists():
                df = read_frame(reservations.values('delete_yn', 'member__gender'))
                if not df.empty:
                    gender_total = df.groupby('member__gender').size().to_dict()
                    gender_cancelled = df[df['delete_yn'] == 1].groupby('member__gender').size().to_dict()
                    
                    dynamic_stats['cancellation_by_gender'] = {}
                    for gender in gender_total.keys():
                        total = gender_total.get(gender, 0)
                        cancelled_count = gender_cancelled.get(gender, 0)
                        rate = round((cancelled_count / total * 100) if total > 0 else 0, 2)
                        dynamic_stats['cancellation_by_gender'][str(gender)] = {
                            'total': int(total),
                            'cancelled': int(cancelled_count),
                            'rate': rate
                        }
        
        # 성별별 예약율
        if 'gender_reservation_rate' in needs:
            reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            ).select_related('member')
            
            if reservations.exists():
                df = read_frame(reservations.values('member__gender'))
                if not df.empty:
                    gender_counts = df.groupby('member__gender').size().to_dict()
                    total_reservations = len(df)
                    
                    dynamic_stats['reservation_by_gender'] = {}
                    for gender, count in gender_counts.items():
                        rate = round((count / total_reservations * 100) if total_reservations > 0 else 0, 2)
                        dynamic_stats['reservation_by_gender'][str(gender)] = {
                            'count': int(count),
                            'rate': rate
                        }
        
        # 지역별 예약 통계
        if 'region_reservation_stats' in needs:
            # 모집글을 통해 지역별 통계 추출 (예약이 연결된 모집글 기준)
            communities = Community.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            ).select_related('reservation_id')
            
            if communities.exists():
                region_stats = {}
                for community in communities:
                    region = community.region
                    if region not in region_stats:
                        region_stats[region] = {'total': 0, 'cancelled': 0, 'active': 0}
                    
                    if community.reservation_id:
                        region_stats[region]['total'] += 1
                        if community.reservation_id.delete_yn == 1:
                            region_stats[region]['cancelled'] += 1
                        else:
                            region_stats[region]['active'] += 1
                
                dynamic_stats['reservations_by_region'] = {
                    str(k): {
                        'total': v['total'],
                        'cancelled': v['cancelled'],
                        'active': v['active']
                    }
                    for k, v in region_stats.items()
                }
        
        # 지역별 모집글 통계
        if 'region_community_stats' in needs:
            communities = Community.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            )
            
            if communities.exists():
                df = read_frame(communities.values('region', 'view_cnt'))
                if not df.empty:
                    region_stats = df.groupby('region').agg({
                        'region': 'count',
                        'view_cnt': 'mean'
                    }).to_dict()
                    dynamic_stats['communities_by_region'] = {
                        'count': {str(k): int(v) for k, v in region_stats.get('region', {}).items()},
                        'avg_views': {str(k): round(float(v), 2) for k, v in region_stats.get('view_cnt', {}).items()}
                    }
        
        # 종목별 예약 통계
        if 'sport_reservation_stats' in needs:
            communities = Community.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            )
            
            if communities.exists():
                df = read_frame(communities.values('sport_type'))
                if not df.empty:
                    sport_counts = df.groupby('sport_type').size().to_dict()
                    dynamic_stats['reservations_by_sport'] = {
                        str(k): int(v) for k, v in sport_counts.items()
                    }
        
        # 종목별 취소율
        if 'sport_cancellation_rate' in needs:
            # 모집글과 예약을 연결해서 종목별 취소율 계산
            communities = Community.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            ).select_related('reservation_id')
            
            if communities.exists():
                sport_cancellation = {}
                for community in communities:
                    sport = community.sport_type
                    if sport not in sport_cancellation:
                        sport_cancellation[sport] = {'total': 0, 'cancelled': 0}
                    
                    # 예약이 연결된 경우
                    if community.reservation_id:
                        sport_cancellation[sport]['total'] += 1
                        if community.reservation_id.delete_yn == 1:
                            sport_cancellation[sport]['cancelled'] += 1
                    else:
                        # 예약이 없는 모집글도 카운트 (취소는 아니지만 전체 통계에 포함)
                        sport_cancellation[sport]['total'] += 1
                
                dynamic_stats['cancellation_by_sport'] = {
                    str(k): {
                        'total': v['total'],
                        'cancelled': v['cancelled'],
                        'rate': round((v['cancelled'] / v['total'] * 100) if v['total'] > 0 else 0, 2)
                    }
                    for k, v in sport_cancellation.items()
                }
        
        # 시간대별 취소율
        if 'hourly_cancellation_stats' in needs:
            cancelled_reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=1
            )
            
            if cancelled_reservations.exists():
                df = read_frame(cancelled_reservations.values('reg_date'))
                if not df.empty:
                    df['hour'] = pd.to_datetime(df['reg_date']).dt.hour
                    hourly_cancelled = df.groupby('hour').size().to_dict()
                    dynamic_stats['cancellation_by_hour'] = {
                        int(k): int(v) for k, v in hourly_cancelled.items()
                    }
        
        # 요일별 취소율 (상세)
        if 'weekday_cancellation_rate' in needs:
            reservations = Reservation.objects.filter(
                reg_date__gte=start_date
            )
            
            if reservations.exists():
                df = read_frame(reservations.values('reg_date', 'delete_yn'))
                if not df.empty:
                    df['weekday'] = pd.to_datetime(df['reg_date']).dt.day_name()
                    weekday_total = df.groupby('weekday').size().to_dict()
                    weekday_cancelled = df[df['delete_yn'] == 1].groupby('weekday').size().to_dict()
                    
                    dynamic_stats['cancellation_by_weekday'] = {}
                    for weekday in weekday_total.keys():
                        total = weekday_total.get(weekday, 0)
                        cancelled = weekday_cancelled.get(weekday, 0)
                        rate = round((cancelled / total * 100) if total > 0 else 0, 2)
                        dynamic_stats['cancellation_by_weekday'][str(weekday)] = {
                            'total': int(total),
                            'cancelled': int(cancelled),
                            'rate': rate
                        }
        
        # 시설 인기도
        if 'facility_popularity' in needs:
            facilities = FacilityInfo.objects.filter(
                view_cnt__gt=0
            ).order_by('-view_cnt')[:20]
            
            dynamic_stats['top_facilities_detailed'] = [
                {
                    'faci_nm': f.faci_nm,
                    'address': f.address,
                    'view_cnt': f.view_cnt,
                    'rs_posible': f.rs_posible,
                }
                for f in facilities
            ]
        
        # ============================================
        # 안전 통계 동적 계산
        # ============================================
        
        # 안전 등급별 상세 통계
        if 'safety_grade_stats' in needs or 'safety_overview' in needs:
            facilities = Facility.objects.exclude(
                schk_visit_ymd__isnull=True
            ).exclude(schk_visit_ymd='')
            
            if facilities.exists():
                df = read_frame(facilities.values('schk_tot_grd_nm', 'schk_tot_grd_cd'))
                if not df.empty:
                    grade_stats = df.groupby('schk_tot_grd_nm').size().to_dict()
                    total = len(df)
                    
                    dynamic_stats['safety_grade_detailed'] = {
                        str(k): {
                            'count': int(v),
                            'percentage': round((v / total * 100) if total > 0 else 0, 2)
                        }
                        for k, v in grade_stats.items() if pd.notna(k)
                    }
        
        # 지역별 안전 통계 (상세)
        if 'safety_region_stats' in needs:
            facilities = Facility.objects.exclude(
                schk_visit_ymd__isnull=True
            ).exclude(schk_visit_ymd='').exclude(cp_nm__isnull=True).exclude(cp_nm='')
            
            if facilities.exists():
                df = read_frame(facilities.values('cp_nm', 'schk_tot_grd_nm'))
                if not df.empty:
                    region_safety = {}
                    for region in df['cp_nm'].dropna().unique():
                        region_df = df[df['cp_nm'] == region]
                        grade_counts = region_df['schk_tot_grd_nm'].value_counts()
                        
                        # 등급별 비율 계산
                        total = len(region_df)
                        region_safety[str(region)] = {
                            'total': int(total),
                            'grades': {
                                str(k): {
                                    'count': int(v),
                                    'percentage': round((v / total * 100) if total > 0 else 0, 2)
                                }
                                for k, v in grade_counts.items() if pd.notna(k)
                            }
                        }
                    
                    dynamic_stats['safety_region_detailed'] = region_safety
        
        # 종목별 안전 통계 (상세)
        if 'safety_sport_stats' in needs:
            facilities = Facility.objects.exclude(
                schk_visit_ymd__isnull=True
            ).exclude(schk_visit_ymd='').exclude(fcob_nm__isnull=True).exclude(fcob_nm='')
            
            if facilities.exists():
                df = read_frame(facilities.values('fcob_nm', 'schk_tot_grd_nm'))
                if not df.empty:
                    sport_safety = {}
                    for sport in df['fcob_nm'].dropna().unique():
                        sport_df = df[df['fcob_nm'] == sport]
                        grade_counts = sport_df['schk_tot_grd_nm'].value_counts()
                        
                        # 등급별 비율 계산
                        total = len(sport_df)
                        sport_safety[str(sport)] = {
                            'total': int(total),
                            'grades': {
                                str(k): {
                                    'count': int(v),
                                    'percentage': round((v / total * 100) if total > 0 else 0, 2)
                                }
                                for k, v in grade_counts.items() if pd.notna(k)
                            }
                        }
                    
                    dynamic_stats['safety_sport_detailed'] = sport_safety
        
        # 연도별 안전 점검 트렌드 (상세)
        if 'safety_yearly_trend' in needs:
            facilities = Facility.objects.exclude(
                schk_visit_ymd__isnull=True
            ).exclude(schk_visit_ymd='')
            
            if facilities.exists():
                df = read_frame(facilities.values('schk_visit_ymd', 'schk_tot_grd_nm'))
                if not df.empty:
                    df['year'] = df['schk_visit_ymd'].str[:4]
                    df['year_int'] = pd.to_numeric(df['year'], errors='coerce')
                    current_year = timezone.now().year
                    valid_df = df[(df['year_int'] >= 2000) & (df['year_int'] <= current_year)]
                    
                    if not valid_df.empty:
                        yearly_trend = {}
                        for year in valid_df['year'].dropna().unique():
                            year_df = valid_df[valid_df['year'] == year]
                            grade_counts = year_df['schk_tot_grd_nm'].value_counts()
                            
                            yearly_trend[str(year)] = {
                                'total': int(len(year_df)),
                                'grades': {str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)}
                            }
                        
                        dynamic_stats['safety_yearly_trend_detailed'] = yearly_trend
        
        # 안전 개선 제안을 위한 위험 시설 식별
        if 'safety_recommendations' in needs:
            facilities = Facility.objects.exclude(
                schk_visit_ymd__isnull=True
            ).exclude(schk_visit_ymd='')
            
            if facilities.exists():
                # 낮은 등급 시설 식별 (등급 코드가 낮거나 등급명에 '낮음', '불량' 등이 포함된 경우)
                low_grade_facilities = facilities.filter(
                    schk_tot_grd_cd__in=['1', '2', '3', '4', '5']
                ) | facilities.filter(
                    schk_tot_grd_nm__icontains='불량'
                ) | facilities.filter(
                    schk_tot_grd_nm__icontains='낮음'
                )
                
                dynamic_stats['safety_risk_facilities'] = [
                    {
                        'faci_nm': f.faci_nm,
                        'faci_addr': f.faci_addr,
                        'schk_tot_grd_nm': f.schk_tot_grd_nm,
                        'schk_tot_grd_cd': f.schk_tot_grd_cd,
                        'schk_visit_ymd': f.schk_visit_ymd,
                        'cp_nm': f.cp_nm,
                        'fcob_nm': f.fcob_nm,
                    }
                    for f in low_grade_facilities[:30]  # 최대 30개
                ]
        
    except Exception as e:
        print(f"동적 통계 계산 오류: {e}")
    
    return dynamic_stats


def collect_stats_data(start_date):
    """
    상세한 통계 데이터 수집 (요일별, 시간대별, 지역별, 종목별 포함)
    """
    stats = {
        'kpi_data': {},
        'daily_reservations': {},
        'daily_members': {},
        'daily_recruitment': {},
        'cancellation_rate': 0,
        'daily_cancellation_rate': {},
        'participation_rate': 0,
        'daily_participation_rate': {},
        'gender_data': {},
        'board_stats': [],
        # 추가 상세 통계
        'weekday_reservations': {},
        'weekday_communities': {},
        'hourly_reservations': {},
        'region_distribution': {},
        'sport_distribution': {},
        'region_sport_combination': {},
        'previous_period_comparison': {},
        'trend_analysis': {},
        # 실제 DB 데이터 (개인정보 제외)
        'recent_reservations': [],
        'recent_communities': [],
        'top_facilities': [],
        'active_member_summary': {},
        'safety_stats': {   
            'total_inspected_facilities': 0,
            'yearly_inspection_trend': {},
            'grade_distribution': {},
            'region_safety_stats': {},
            'sport_safety_stats': {},
            'recent_inspections': [],
        },
    }
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        from django_pandas.io import read_frame
        import pandas as pd
        import numpy as np
        
        # KPI 데이터
        today = timezone.now().date()
        try:
            stats['kpi_data'] = {
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
                'total_reservations': Reservation.objects.filter(reg_date__gte=start_date, delete_yn=0).count(),
                'total_communities': Community.objects.filter(reg_date__gte=start_date, delete_date__isnull=True).count(),
                'total_members': Member.objects.filter(reg_date__gte=start_date, delete_yn=0).count(),
            }
        except Exception:
            pass
        
        # 예약 추이 및 요일별 분석
        try:
            reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            )
            if reservations.exists():
                df = read_frame(reservations.values('reg_date'))
                if not df.empty:
                    df['date'] = pd.to_datetime(df['reg_date']).dt.date
                    df['weekday'] = pd.to_datetime(df['reg_date']).dt.day_name()
                    df['hour'] = pd.to_datetime(df['reg_date']).dt.hour
                    
                    # 일별 추이
                    daily = df.groupby('date').size().to_dict()
                    stats['daily_reservations'] = {str(k): int(v) for k, v in daily.items()}
                    
                    # 요일별 통계
                    weekday_stats = df.groupby('weekday').size().to_dict()
                    stats['weekday_reservations'] = {str(k): int(v) for k, v in weekday_stats.items()}
                    
                    # 시간대별 통계
                    hourly_stats = df.groupby('hour').size().to_dict()
                    stats['hourly_reservations'] = {int(k): int(v) for k, v in hourly_stats.items()}
                    
                    # 통계 계산
                    if len(daily) > 0:
                        daily_values = list(daily.values())
                        stats['trend_analysis']['reservations'] = {
                            'average': round(np.mean(daily_values), 2),
                            'max': int(np.max(daily_values)),
                            'min': int(np.min(daily_values)),
                            'std': round(np.std(daily_values), 2),
                            'trend': 'increasing' if len(daily_values) > 1 and daily_values[-1] > daily_values[0] else 'decreasing'
                        }
        except Exception as e:
            print(f"예약 통계 수집 오류: {e}")
        
        # 취소율 및 취소 패턴
        try:
            total_reservations = Reservation.objects.filter(reg_date__gte=start_date).count()
            cancelled = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=1
            ).count()
            stats['cancellation_rate'] = round((cancelled / total_reservations * 100) if total_reservations > 0 else 0, 2)
            
            # 취소된 예약의 요일별 패턴
            cancelled_reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=1
            )
            if cancelled_reservations.exists():
                df_cancelled = read_frame(cancelled_reservations.values('reg_date'))
                if not df_cancelled.empty:
                    df_cancelled['weekday'] = pd.to_datetime(df_cancelled['reg_date']).dt.day_name()
                    weekday_cancelled = df_cancelled.groupby('weekday').size().to_dict()
                    stats['weekday_cancellations'] = {str(k): int(v) for k, v in weekday_cancelled.items()}
        except Exception:
            pass
        
        # 회원 가입 추이 및 요일별 분석
        try:
            members = Member.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            )
            if members.exists():
                df = read_frame(members.values('reg_date'))
                if not df.empty:
                    df['date'] = pd.to_datetime(df['reg_date']).dt.date
                    df['weekday'] = pd.to_datetime(df['reg_date']).dt.day_name()
                    daily = df.groupby('date').size().to_dict()
                    stats['daily_members'] = {str(k): int(v) for k, v in daily.items()}
                    
                    weekday_stats = df.groupby('weekday').size().to_dict()
                    stats['weekday_members'] = {str(k): int(v) for k, v in weekday_stats.items()}
        except Exception:
            pass
        
        # 성별 분포
        try:
            gender_dist = Member.objects.filter(delete_yn=0).values('gender').annotate(
                count=Count('member_id')
            )
            stats['gender_data'] = {str(item['gender']): item['count'] for item in gender_dist}
        except Exception:
            pass
        
        # 모집글 추이 및 상세 분석
        try:
            communities = Community.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            )
            if communities.exists():
                df = read_frame(communities.values('reg_date', 'region', 'sport_type', 'view_cnt'))
                if not df.empty:
                    df['date'] = pd.to_datetime(df['reg_date']).dt.date
                    df['weekday'] = pd.to_datetime(df['reg_date']).dt.day_name()
                    
                    # 일별 추이
                    daily = df.groupby('date').size().to_dict()
                    stats['daily_recruitment'] = {str(k): int(v) for k, v in daily.items()}
                    
                    # 요일별 통계
                    weekday_stats = df.groupby('weekday').size().to_dict()
                    stats['weekday_communities'] = {str(k): int(v) for k, v in weekday_stats.items()}
                    
                    # 지역별 분포
                    region_stats = df.groupby('region').size().to_dict()
                    stats['region_distribution'] = {str(k): int(v) for k, v in region_stats.items()}
                    
                    # 종목별 분포
                    sport_stats = df.groupby('sport_type').size().to_dict()
                    stats['sport_distribution'] = {str(k): int(v) for k, v in sport_stats.items()}
                    
                    # 지역-종목 조합
                    region_sport = df.groupby(['region', 'sport_type']).size().reset_index(name='count')
                    stats['region_sport_combination'] = region_sport.to_dict('records')
                    
                    # 평균 조회수
                    if 'view_cnt' in df.columns:
                        avg_views = df.groupby('sport_type')['view_cnt'].mean().to_dict()
                        stats['avg_views_by_sport'] = {str(k): round(float(v), 2) for k, v in avg_views.items()}
        except Exception as e:
            print(f"모집글 통계 수집 오류: {e}")
        
        # 참여율
        try:
            join_stats = JoinStat.objects.select_related('community_id').filter(
                community_id__reg_date__gte=start_date
            )
            if join_stats.exists():
                df = read_frame(join_stats.values('community_id__reg_date', 'join_status', 'community_id__sport_type', 'community_id__region'))
                if not df.empty:
                    total_joins = len(df)
                    completed_joins = len(df[df['join_status'] == 1])
                    stats['participation_rate'] = round((completed_joins / total_joins * 100) if total_joins > 0 else 0, 2)
                    
                    # 종목별 참여율
                    if 'community_id__sport_type' in df.columns:
                        sport_participation = df.groupby('community_id__sport_type').apply(
                            lambda x: round((x['join_status'] == 1).sum() / len(x) * 100, 2)
                        ).to_dict()
                        stats['participation_by_sport'] = {str(k): float(v) for k, v in sport_participation.items()}
        except Exception as e:
            print(f"참여율 통계 수집 오류: {e}")
        
        # 이전 기간과 비교
        try:
            period_days = (timezone.now() - start_date).days
            previous_start = start_date - timedelta(days=period_days)
            
            prev_reservations = Reservation.objects.filter(
                reg_date__gte=previous_start,
                reg_date__lt=start_date,
                delete_yn=0
            ).count()
            curr_reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            ).count()
            
            if prev_reservations > 0:
                change_rate = round(((curr_reservations - prev_reservations) / prev_reservations * 100), 2)
                stats['previous_period_comparison']['reservations'] = {
                    'previous': prev_reservations,
                    'current': curr_reservations,
                    'change_rate': change_rate,
                    'change_direction': 'increase' if change_rate > 0 else 'decrease'
                }
        except Exception:
            pass
        
        # ============================================
        # 실제 DB 데이터 수집 (개인정보 제외)
        # ============================================
        
        # 최근 예약 목록 (개인정보 제외)
        try:
            recent_reservations = Reservation.objects.filter(
                reg_date__gte=start_date,
                delete_yn=0
            ).select_related('member').order_by('-reg_date')[:20]
            
            stats['recent_reservations'] = [
                {
                    'reservation_id': r.reservation_id,
                    'reservation_num': r.reservation_num,
                    'reg_date': str(r.reg_date),
                    'member_id': r.member.member_id,  # ID만
                    'member_user_id': r.member.user_id,  # 아이디만 (개인정보 아님)
                    'member_nickname': r.member.nickname,  # 닉네임만
                    'member_gender': r.member.gender,  # 성별 (통계용)
                }
                for r in recent_reservations
            ]
        except Exception as e:
            print(f"최근 예약 데이터 수집 오류: {e}")
        
        # 최근 모집글 목록
        try:
            recent_communities = Community.objects.filter(
                reg_date__gte=start_date,
                delete_date__isnull=True
            ).select_related('member_id').order_by('-reg_date')[:20]
            
            stats['recent_communities'] = [
                {
                    'community_id': c.community_id,
                    'title': c.title,
                    'region': c.region,
                    'region2': c.region2,
                    'sport_type': c.sport_type,
                    'facility': c.facility,
                    'num_member': c.num_member,
                    'view_cnt': c.view_cnt,
                    'reg_date': str(c.reg_date),
                    'member_id': c.member_id.member_id,  # ID만
                    'member_user_id': c.member_id.user_id,  # 아이디만
                    'member_nickname': c.member_id.nickname,  # 닉네임만
                }
                for c in recent_communities
            ]
        except Exception as e:
            print(f"최근 모집글 데이터 수집 오류: {e}")
        
        # 인기 시설 목록 (조회수 기준)
        try:
            top_facilities = FacilityInfo.objects.filter(
                view_cnt__gt=0
            ).order_by('-view_cnt')[:15]
            
            stats['top_facilities'] = [
                {
                    'facility_id': f.facility_id,
                    'faci_nm': f.faci_nm,
                    'address': f.address,
                    'sido': f.sido,
                    'sigugun': f.sigugun,
                    'view_cnt': f.view_cnt,
                    'rs_posible': f.rs_posible,
                    'reg_date': str(f.reg_date) if f.reg_date else None,
                }
                for f in top_facilities
            ]
        except Exception as e:
            print(f"인기 시설 데이터 수집 오류: {e}")
        
        # 활성 회원 요약 (개인정보 제외)
        try:
            active_members = Member.objects.filter(delete_yn=0)
            stats['active_member_summary'] = {
                'total_count': active_members.count(),
                'recent_count': active_members.filter(reg_date__gte=start_date).count(),
                'gender_distribution': dict(active_members.values('gender').annotate(count=Count('member_id')).values_list('gender', 'count')),
                # 개인정보는 포함하지 않음
            }
        except Exception as e:
            print(f"활성 회원 요약 수집 오류: {e}")
        
        # ============================================
        # 안전 통계 데이터 수집 (데이터 업데이트 시 자동 반영)
        # ============================================
        try:
            from facility.models import Facility
            
            # 안전점검 데이터가 있는 시설만 조회
            inspected_facilities = Facility.objects.exclude(
                schk_visit_ymd__isnull=True
            ).exclude(schk_visit_ymd='')
            
            stats['safety_stats']['total_inspected_facilities'] = inspected_facilities.count()
            
            if inspected_facilities.exists():
                df_safety = read_frame(inspected_facilities.values(
                    'schk_visit_ymd', 'schk_tot_grd_nm', 'schk_tot_grd_cd',
                    'cp_nm', 'fcob_nm', 'faci_nm', 'faci_addr'
                ))
                
                if not df_safety.empty:
                    # 연도별 점검 추세
                    df_safety['year'] = df_safety['schk_visit_ymd'].str[:4]
                    df_safety['year_int'] = pd.to_numeric(df_safety['year'], errors='coerce')
                    current_year = timezone.now().year
                    valid_df = df_safety[(df_safety['year_int'] >= 2000) & (df_safety['year_int'] <= current_year)]
                    
                    if not valid_df.empty:
                        yearly_trend = valid_df.groupby('year').size()
                        min_year = int(valid_df['year'].min())
                        max_year = current_year
                        
                        stats['safety_stats']['yearly_inspection_trend'] = {
                            str(year): int(yearly_trend.get(str(year), 0))
                            for year in range(min_year, max_year + 1)
                        }
                    
                    # 등급별 분포
                    grade_dist = df_safety['schk_tot_grd_nm'].value_counts()
                    stats['safety_stats']['grade_distribution'] = {
                        str(k): int(v) for k, v in grade_dist.items() if pd.notna(k)
                    }
                    
                    # 지역별 안전 통계
                    if 'cp_nm' in df_safety.columns:
                        for region in df_safety['cp_nm'].dropna().unique():
                            region_df = df_safety[df_safety['cp_nm'] == region]
                            grade_counts = region_df['schk_tot_grd_nm'].value_counts()
                            stats['safety_stats']['region_safety_stats'][str(region)] = {
                                'total': len(region_df),
                                'grades': {str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)}
                            }
                    
                    # 종목별 안전 통계
                    if 'fcob_nm' in df_safety.columns:
                        for sport in df_safety['fcob_nm'].dropna().unique():
                            sport_df = df_safety[df_safety['fcob_nm'] == sport]
                            grade_counts = sport_df['schk_tot_grd_nm'].value_counts()
                            stats['safety_stats']['sport_safety_stats'][str(sport)] = {
                                'total': len(sport_df),
                                'grades': {str(k): int(v) for k, v in grade_counts.items() if pd.notna(k)}
                            }
                    
                    # 최근 점검 시설 목록 (최근 20개)
                    recent_inspected = inspected_facilities.order_by('-schk_visit_ymd')[:20]
                    stats['safety_stats']['recent_inspections'] = [
                        {
                            'faci_nm': f.faci_nm,
                            'faci_addr': f.faci_addr,
                            'schk_visit_ymd': f.schk_visit_ymd,
                            'schk_tot_grd_nm': f.schk_tot_grd_nm,
                            'schk_tot_grd_cd': f.schk_tot_grd_cd,
                            'cp_nm': f.cp_nm,
                            'fcob_nm': f.fcob_nm,
                        }
                        for f in recent_inspected
                    ]
        except Exception as e:
            print(f"안전 통계 데이터 수집 오류: {e}")
        
    except Exception as e:
        print(f"통계 데이터 수집 중 오류: {e}")
    
    return stats


def ai_analytics_dashboard(request):
    """
    AI 분석 대시보드
    페이지 로드 시에는 분석을 수행하지 않고, AJAX로만 분석하도록 변경
    """
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    # 필터 파라미터
    date_range = request.GET.get('date_range', '7')
    analysis_type = request.GET.get('analysis_type', 'overview')
    
    try:
        days = int(date_range)
    except (ValueError, TypeError):
        days = 7
    
    start_date = timezone.now() - timedelta(days=days)
    
    # 통계 데이터 수집 (빠르게 수집 가능)
    stats_data = collect_stats_data(start_date)
    
    # 페이지 로드 시에는 AI 분석을 수행하지 않음
    # 사용자가 '분석 새로고침' 버튼을 클릭할 때만 AJAX로 분석 수행
    ai_insights = None
    ai_insights_html = None
    error_message = None
    
    context = {
        'stats_data': stats_data,
        'ai_insights': ai_insights,
        'ai_insights_html': ai_insights_html,
        'error_message': error_message,
        'date_range': date_range,
        'analysis_type': analysis_type,
    }
    
    return render(request, 'ai_analytics/dashboard.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def ai_analyze_ajax(request):
    """
    AJAX로 AI 분석 요청 (캐싱 적용)
    """
    if not is_manager(request):
        return JsonResponse({'success': False, 'error': '관리자 권한이 필요합니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        analysis_type = data.get('analysis_type', 'overview')
        date_range = data.get('date_range', '7')
        
        try:
            days = int(date_range)
        except (ValueError, TypeError):
            days = 7
        
        start_date = timezone.now() - timedelta(days=days)
        stats_data = collect_stats_data(start_date)
        
        # 캐시 키 생성 (날짜 범위, 분석 유형, 통계 데이터 해시 기반)
        stats_hash = hashlib.md5(json.dumps(stats_data, sort_keys=True).encode()).hexdigest()[:8]
        cache_key = f"ai_analysis_{date_range}_{analysis_type}_{stats_hash}"
        
        # 캐시에서 확인 (1시간 캐시)
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({
                'success': True,
                'insights': cached_result.get('insights'),
                'insights_html': cached_result.get('insights_html'),
                'cached': True
            })
        
        # 캐시에 없으면 AI 분석 수행
        ai_service = AIAnalyticsService()
        ai_insights = None
        
        if analysis_type == 'overview':
            ai_insights = ai_service.analyze_dashboard_stats(stats_data)
        elif analysis_type == 'reservations':
            reservation_data = {
                'daily_reservations': stats_data.get('daily_reservations', {}),
                'cancellation_rate': stats_data.get('cancellation_rate', 0),
                'daily_cancellation_rate': stats_data.get('daily_cancellation_rate', {}),
                'weekday_reservations': stats_data.get('weekday_reservations', {}),
                'hourly_reservations': stats_data.get('hourly_reservations', {}),
            }
            ai_insights = ai_service.analyze_reservation_patterns(reservation_data)
        elif analysis_type == 'members':
            member_data = {
                'daily_members': stats_data.get('daily_members', {}),
                'gender_data': stats_data.get('gender_data', {}),
                'weekday_members': stats_data.get('weekday_members', {}),
            }
            ai_insights = ai_service.analyze_member_behavior(member_data)
        elif analysis_type == 'anomalies':
            ai_insights = ai_service.detect_anomalies(stats_data)
        
        # 마크다운을 HTML로 변환
        ai_insights_html = None
        if ai_insights:
            html = markdown.markdown(ai_insights, extensions=['extra', 'codehilite', 'nl2br'])
            allowed_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'br', 'hr']
            ai_insights_html = bleach.clean(html, tags=allowed_tags, strip=True)
            
            # 결과를 캐시에 저장 (1시간 = 3600초)
            cache.set(cache_key, {
                'insights': ai_insights,
                'insights_html': ai_insights_html
            }, 3600)
        
        return JsonResponse({
            'success': True,
            'insights': ai_insights,
            'insights_html': ai_insights_html,
            'cached': False
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def ai_chat_ajax(request):
    """
    AI 채팅 분석 요청 (멀티턴 대화 지원)
    GET 요청도 허용 (스트리밍용)
    """
    if not is_manager(request):
        return JsonResponse({'success': False, 'error': '관리자 권한이 필요합니다.'}, status=403)
    
    try:
        # GET 요청만 지원 (스트리밍용 EventSource)
        if request.method != 'GET':
            return JsonResponse({
                'success': False,
                'error': 'GET 요청만 지원됩니다.'
            }, status=405)
        
        user_message = request.GET.get('message', '').strip()
        date_range = request.GET.get('date_range', '7')
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': '질문을 입력해주세요.'
            }, status=400)
        
        try:
            days = int(date_range)
        except (ValueError, TypeError):
            days = 7
        
        start_date = timezone.now() - timedelta(days=days)
        
        # 기본 통계 데이터 수집
        stats_data = collect_stats_data(start_date)
        
        # 사용자 질문 분석 및 동적 통계 계산 (하이브리드 방식)
        question_needs = analyze_question_needs(user_message)
        if question_needs:
            dynamic_stats = calculate_dynamic_stats(question_needs, start_date)
            # 동적 통계를 기본 통계에 병합
            stats_data.update(dynamic_stats)
            # 동적으로 계산된 통계임을 표시
            stats_data['_dynamic_calculated'] = True
            stats_data['_calculated_stats'] = question_needs
        
        # 세션에서 대화 히스토리 가져오기
        session_key = f'ai_chat_history_{date_range}'
        conversation_history = request.session.get(session_key, [])
        
        ai_service = AIAnalyticsService()
        
        # 스트리밍 응답 (Server-Sent Events)
        from django.http import StreamingHttpResponse
        import json as json_module
        
        def generate():
            full_response = ""
            try:
                for chunk in ai_service.chat_analysis_stream(user_message, stats_data, conversation_history):
                    full_response += chunk
                    yield f"data: {json_module.dumps({'chunk': chunk, 'done': False})}\n\n"
                
                # 대화 히스토리 업데이트
                conversation_history.append({"role": "user", "content": user_message})
                conversation_history.append({"role": "assistant", "content": full_response})
                # 최근 20개만 유지
                request.session[session_key] = conversation_history[-20:]
                request.session.save()
                
                yield f"data: {json_module.dumps({'chunk': '', 'done': True})}\n\n"
            except Exception as e:
                error_msg = f"⚠️ 오류 발생: {str(e)}"
                yield f"data: {json_module.dumps({'chunk': error_msg, 'done': True})}\n\n"
        
        response = StreamingHttpResponse(generate(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # nginx 버퍼링 방지
        return response
    
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ai_chat_clear(request):
    """
    대화 히스토리 초기화
    """
    if not is_manager(request):
        return JsonResponse({'success': False, 'error': '관리자 권한이 필요합니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        date_range = data.get('date_range', '7')
        session_key = f'ai_chat_history_{date_range}'
        
        if session_key in request.session:
            del request.session[session_key]
            request.session.save()
        
        return JsonResponse({
            'success': True,
            'message': '대화 히스토리가 초기화되었습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def ai_chat_export(request):
    """
    대화 히스토리 내보내기 (텍스트 파일)
    """
    if not is_manager(request):
        from django.http import HttpResponse
        return HttpResponse('관리자 권한이 필요합니다.', status=403)
    
    try:
        date_range = request.GET.get('date_range', '7')
        session_key = f'ai_chat_history_{date_range}'
        conversation_history = request.session.get(session_key, [])
        
        if not conversation_history:
            from django.http import HttpResponse
            return HttpResponse('내보낼 대화가 없습니다.', status=404)
        
        # 텍스트 형식으로 변환
        export_text = f"AI 분석 대화 내보내기 (기간: 최근 {date_range}일)\n"
        export_text += "=" * 50 + "\n\n"
        
        for msg in conversation_history:
            role = "사용자" if msg['role'] == 'user' else "AI 분석가"
            export_text += f"[{role}]\n{msg['content']}\n\n"
        
        from django.http import HttpResponse
        response = HttpResponse(export_text, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="ai_chat_export_{date_range}days_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt"'
        return response
    
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f'오류 발생: {str(e)}', status=500)
