import os
import random
import re
import string
from datetime import timedelta
from urllib.parse import quote

import requests
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from manager.models import HeroImg
from member.models import Member


# ------------------------- 공통 유틸 / API ------------------------- #

def weather_api(request):
    """
    메인 페이지 오늘의 날씨 위젯용 기상청 초단기실황 API 프록시
    - 기본 도시는 서울(seoul)
    - 쿼리 파라미터: ?city=seoul|busan|incheon|daejeon|daegu|gwangju
    """
    SERVICE_KEY = os.getenv("OPEN_WEATHER_KEY")
    if not SERVICE_KEY:
        return JsonResponse({"error": "OPEN_WEATHER_KEY is not configured"}, status=500)

    city_code = (request.GET.get("city") or "seoul").lower()

    # 기상청 격자 좌표 (nx, ny)
    city_map = {
        "seoul":   {"nx": 60,  "ny": 127, "label": "서울"},
        "busan":   {"nx": 98,  "ny": 76,  "label": "부산"},
        "incheon": {"nx": 55,  "ny": 124, "label": "인천"},
        "daejeon": {"nx": 67,  "ny": 100, "label": "대전"},
        "daegu":   {"nx": 89,  "ny": 90,  "label": "대구"},
        "gwangju": {"nx": 58,  "ny": 74,  "label": "광주"},
        "ulsan":    {"nx": 102, "ny": 84,  "label": "울산"},
        "jeju":     {"nx": 53,  "ny": 38,  "label": "제주"},
        "suwon":    {"nx": 60,  "ny": 121, "label": "수원"},
        "cheongju": {"nx": 69,  "ny": 106, "label": "청주"},
        "jeonju":   {"nx": 63,  "ny": 89,  "label": "전주"},
    }
    city_info = city_map.get(city_code, city_map["seoul"])

    # 기준 시각(직전 정시)
    now = timezone.now()
    base_time_dt = now - timedelta(hours=1)
    base_date = base_time_dt.strftime("%Y%m%d")
    base_time = base_time_dt.strftime("%H00")

    endpoint = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": 100,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": city_info["nx"],
        "ny": city_info["ny"],
    }

    try:
        resp = requests.get(endpoint, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[ERROR] weather_api(KMA) 호출 실패: {e}")
        return JsonResponse({"error": "weather_api_failed"}, status=500)

    try:
        items = data["response"]["body"]["items"]["item"]
    except Exception as e:
        print(f"[ERROR] weather_api(KMA) 응답 파싱 실패: {e}")
        return JsonResponse({"error": "weather_api_parse_error"}, status=500)

    values = {}
    for it in items:
        cat = it.get("category")
        val = it.get("obsrValue")
        values[cat] = val

    # 기온 / 습도 / 강수량 / 풍속 / 강수형태 / 하늘상태
    temp = float(values.get("T1H", 0))
    humidity = float(values.get("REH", 0))
    wind_speed = float(values.get("WSD", 0))

    rn1_raw = values.get("RN1", "0")
    try:
        precipitation = float(rn1_raw)
    except ValueError:
        precipitation = 0.0

    pty = str(values.get("PTY", "0"))  # 0 없음, 1 비, 2 비/눈, 3 눈, 5/6/7: 다양한 형태
    sky = str(values.get("SKY", "1"))  # 1 맑음, 3 구름많음, 4 흐림

    # main/description 매핑
    if pty in ("1", "2", "5", "6"):
        main = "Rain"
        description = "비"
    elif pty in ("3", "7"):
        main = "Snow"
        description = "눈"
    else:
        if sky == "1":
            main = "Clear"
            description = "맑음"
        elif sky == "3":
            main = "Clouds"
            description = "구름 많음"
        elif sky == "4":
            main = "Clouds"
            description = "흐림"
        else:
            main = "Clouds"
            description = "구름"

    result = {
        "city_code": city_code,
        "city_label": city_info["label"],
        "city_name": city_info["label"],
        "temp": temp,
        "description": description,
        "main": main,
        "precipitation": precipitation,
        "humidity": humidity,
        "wind_speed": wind_speed,
    }
    return JsonResponse(result)

def index(request):
    # DB에서 랜덤 시설 3개 가져오기
    try:
        from facility.models import FacilityInfo

        all_facilities = FacilityInfo.objects.filter(rs_posible=1)

        if all_facilities.exists():
            facilities_list = list(all_facilities)
            random_facilities = random.sample(facilities_list, min(3, len(facilities_list)))

            facilities = []
            for fac in random_facilities:
                facilities.append({
                    'id': fac.id,
                    'faci_id': fac.facility_id,
                    'name': fac.faci_nm,
                    'address': fac.address,
                    'description': fac.tel if fac.tel else '시설 정보',
                })
        else:
            facilities = []
    except Exception as e:
        print(f"[ERROR] index 함수 시설 데이터 로드 오류: {str(e)}")
        facilities = []

    now = timezone.now()

    banners = HeroImg.objects.filter(
        delete_date__isnull=True
    ).filter(
        Q(img_status=0) |
        Q(img_status=1, start_date__lte=now, end_date__gte=now)
    ).order_by('-img_id')

    context = {
        'random_facilities': facilities,
        'banners': banners,   # ← 이거 추가!
    }

    return render(request, 'common/index.html', context)

def login(request):
    if request.method == "POST":
        user_id = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember")  # 체크박스 여부
        next_url = request.POST.get("next") or request.GET.get("next", "")  # 이전 페이지 URL

        # 아이디 존재 여부
        try:
            user = Member.objects.get(user_id=user_id)
        except Member.DoesNotExist:
            messages.error(request, "존재하지 않는 아이디입니다.")
            return render(request, "common/login.html", {"next": next_url})

        # 비밀번호 체크
        
        if not check_password(password, user.password):
            messages.error(request, "비밀번호가 올바르지 않습니다.")
            context = {"next": next_url} if next_url else {}
            return render(request, "common/login.html", context)
        
        # 탈퇴한 회원
        if user.delete_yn == 1:  
            messages.error(request, "이미 회원 탈퇴한 계정입니다.")
            return render(request, "common/login.html", {"next": next_url})

        # 관리자에 의해 탈퇴 되었을때 
        user = Member.objects.get(user_id=user_id)
        if user.delete_yn ==2:
            messages.error(request, "관리자에의해 탈퇴된 회원입니다. 관리자에게 문의하세요.")
            context = {"next": next_url} if next_url else {}
            return render(request, "common/login.html", context)

        
        # 로그인 성공 → 세션에 저장
        request.session["user_id"] = user.user_id
        request.session["user_name"] = user.name
        request.session["nickname"] = user.nickname
        request.session["is_kakao_user"] = False  # 일반 로그인

        # 관리자 체크 (manager_yn == 1인 경우)
        if user.manager_yn == 1:
            request.session["manager_id"] = user.member_id
            #request.session["manager_name"] = user.name
            # 로그인 유지 선택 시 세션 만료 시간 변경
            if remember:
                request.session.set_expiry(60 * 60)  # 1시간 유지
            else:
                request.session.set_expiry(0)  # 브라우저 닫으면 만료
            
            # 이전 페이지가 있으면 그곳으로, 없으면 관리자 대시보드로
            if next_url:
                return redirect(next_url)
            return redirect("/manager/dashboard/")  # 관리자는 관리자 페이지로

        # 일반 사용자
        # 로그인 유지 선택 시 세션 만료 시간 변경
        if remember:
            request.session.set_expiry(60 * 60)  # 1시간 유지
        else:
            request.session.set_expiry(0)  # 브라우저 닫으면 만료

        # 이전 페이지가 있으면 그곳으로, 없으면 홈으로
        if next_url:
            return redirect(next_url)
        return redirect("/")   # 로그인 후 이동 경로

    # GET 요청: next 파라미터를 템플릿에 전달
    next_url = request.GET.get("next", "")
    context = {"next": next_url} if next_url else {}
    return render(request, "common/login.html", context)

def logout(request):
    """
    로그아웃 처리
    - 카카오 로그인 사용자: 세션 삭제 후 카카오 로그아웃 페이지로 이동
    - 일반 로그인 사용자: 세션 삭제 후 메인 페이지로 이동
    """
    # 로그인하지 않은 경우
    if not request.session.get('user_id'):
        return redirect('/')
    
    # 카카오 로그인 사용자 여부 확인
    is_kakao_user = request.session.get('is_kakao_user', False)
    if not is_kakao_user:
        user_id = request.session.get('user_id', '')
        is_kakao_user = user_id.startswith('kakao_') if user_id else False
    
    # 카카오 로그인 사용자인 경우: 세션 먼저 삭제 후 카카오 로그아웃 페이지로 이동
    if is_kakao_user:
        # 세션의 모든 키를 명시적으로 삭제
        session_keys = list(request.session.keys())
        for key in session_keys:
            del request.session[key]
        
        # 세션 완전히 삭제
        request.session.flush()
        request.session.set_expiry(0)
        
        KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
        if KAKAO_REST_API_KEY:
            # 카카오 로그아웃 후 메인 페이지로 돌아옴 (세션은 이미 삭제됨)
            kakao_logout_url = (
                "https://kauth.kakao.com/oauth/logout"
                f"?client_id={KAKAO_REST_API_KEY}"
                f"&logout_redirect_uri={request.build_absolute_uri('/')}"
            )
            return redirect(kakao_logout_url)
    
    # 일반 로그인 사용자: 세션 삭제 후 메인 페이지로
    # 세션의 모든 키를 명시적으로 삭제
    session_keys = list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    
    # 세션 완전히 삭제
    request.session.flush()
    
    # 세션 쿠키도 삭제하기 위해 만료 시간 설정
    request.session.set_expiry(0)
    
    messages.success(request, "로그아웃되었습니다.")
    return redirect('/')

def kakao_login(request):
    """카카오 로그인 시작"""
    KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
    if not KAKAO_REST_API_KEY:
        messages.error(request, "카카오 로그인 설정이 완료되지 않았습니다.")
        return redirect('/login/')
    
    # next 파라미터 처리
    next_url = request.GET.get('next', '')
    if next_url:
        request.session['kakao_next'] = next_url
    
    # Redirect URI 자동 생성
    REDIRECT_URI = request.build_absolute_uri('/login/kakao/callback/')
    encoded_redirect_uri = quote(REDIRECT_URI, safe='')

    # 카카오 로그인 페이지로 리다이렉트 - 항상 로그인 화면 표시
    kakao_auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={encoded_redirect_uri}"
        "&response_type=code"
        "&prompt=login"  # 항상 로그인 화면 표시 (자동 로그인 방지)
    )
    return redirect(kakao_auth_url)

def kakao_callback(request):
    """카카오 로그인 콜백 처리"""
    # 카카오에서 오류 반환한 경우 처리
    error = request.GET.get('error')
    error_description = request.GET.get('error_description')
    if error:
        messages.error(request, f"카카오 로그인에 실패했습니다: {error_description or error}")
        return redirect('/login/')
    
    code = request.GET.get('code')
    if not code:
        messages.error(request, "카카오 로그인에 실패했습니다.")
        return redirect('/login/')
    
    KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
    if not KAKAO_REST_API_KEY:
        messages.error(request, "카카오 로그인 설정이 완료되지 않았습니다.")
        return redirect('/login/')
    
    # Redirect URI 자동 생성 (환경변수는 무시하고 항상 자동 생성)
    REDIRECT_URI = request.build_absolute_uri('/login/kakao/callback/')
    
    try:
        # 1. 토큰 받기
        token_url = "https://kauth.kakao.com/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': KAKAO_REST_API_KEY,
            'redirect_uri': REDIRECT_URI,
            'code': code
        }
        
        token_response = requests.post(token_url, data=token_data, timeout=10)
        
        # HTTP 상태 코드 확인
        if token_response.status_code != 200:
            messages.error(request, f"카카오 로그인에 실패했습니다. (HTTP {token_response.status_code})")
            return redirect('/login/')
        
        # JSON 파싱
        try:
            token_json = token_response.json()
        except ValueError:
            messages.error(request, "카카오 로그인 응답을 처리하는데 실패했습니다.")
            return redirect('/login/')
        
        if 'error' in token_json:
            error_desc = token_json.get('error_description', token_json.get('error', '알 수 없는 오류'))
            messages.error(request, f"카카오 로그인에 실패했습니다: {error_desc}")
            return redirect('/login/')
        
        access_token = token_json.get('access_token')
        if not access_token:
            messages.error(request, "카카오 로그인에 실패했습니다: 토큰을 받을 수 없습니다.")
            return redirect('/login/')
        
        # 2. 사용자 정보 가져오기
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers, timeout=10)
        
        # HTTP 상태 코드 확인
        if user_response.status_code != 200:
            messages.error(request, f"사용자 정보를 가져오는데 실패했습니다. (HTTP {user_response.status_code})")
            return redirect('/login/')
        
        # JSON 파싱
        try:
            user_info = user_response.json()
        except ValueError:
            messages.error(request, "사용자 정보를 처리하는데 실패했습니다.")
            return redirect('/login/')
        
        if 'error' in user_info:
            error_desc = user_info.get('error_description', user_info.get('error', '알 수 없는 오류'))
            messages.error(request, f"사용자 정보를 가져오는데 실패했습니다: {error_desc}")
            return redirect('/login/')
        
        # 3. 카카오 ID 추출
        try:
            kakao_id = str(user_info['id'])
        except (KeyError, TypeError):
            messages.error(request, "사용자 정보 형식이 올바르지 않습니다.")
            return redirect('/login/')
        
        kakao_account = user_info.get('kakao_account', {})
        profile = kakao_account.get('profile', {})
        nickname = profile.get('nickname', f'카카오사용자_{kakao_id[:6]}')
        
        # 카카오 ID를 user_id로 사용 (kakao_ 접두사 추가)
        kakao_user_id = f'kakao_{kakao_id}'
        
        # 4. 회원 찾기 또는 생성
        try:
            # 기존 회원 찾기
            user = Member.objects.get(user_id=kakao_user_id)
            
            # 탈퇴 여부 확인 (delete_yn으로 체크)
            # delete_yn == 1: 사용자 탈퇴 (재가입 가능)
            # delete_yn == 2: 관리자 탈퇴 (재가입 불가)
            if user.delete_yn == 1:
                # 탈퇴한 카카오 사용자 재가입 처리 (회원 정보 복구)
                # 게시글은 delete_date로 이미 삭제 처리되어 있으므로 자동으로 유지됨
                user.delete_yn = 0
                # delete_date는 유지 (재가입 이력 추적용)
                # delete_reason은 유지 (이력 보관용)
                user.save()
                # 재가입 안내 메시지를 세션에 저장 (로그인 후 팝업으로 표시)
                request.session['kakao_rejoin_message'] = True
            elif user.delete_yn == 2:
                # 관리자에 의해 탈퇴된 경우 재가입 불가
                messages.error(request, "관리자에 의해 탈퇴된 회원입니다. 관리자에게 문의하세요.")
                return redirect('/login/')
            
        except Member.DoesNotExist:
            # 신규 회원: DB에 저장하지 않고 세션에만 저장
            # 닉네임 중복 체크 (나중에 회원가입 시 사용)
            original_nickname = nickname
            counter = 1
            while Member.objects.filter(nickname=nickname).exists():
                nickname = f"{original_nickname}_{counter}"
                counter += 1
            
            # 세션에 카카오 회원가입 정보 저장 (DB 저장 X)
            request.session['kakao_signup_user_id'] = kakao_user_id
            request.session['kakao_signup_name'] = nickname
            request.session['kakao_signup_nickname'] = nickname
            request.session['kakao_signup_mode'] = True
            request.session['kakao_id'] = kakao_id  # 나중에 DB 저장 시 사용
            
            # 약관 동의 페이지로 리다이렉트
            return redirect('common:terms')
        
        # 6. 기존 회원의 경우도 주소 정보 체크 (addr1이 비어있으면 약관 동의 페이지로 - 신규/기존 동일 처리)
        if not user.addr1 or user.addr1.strip() == '':
            # 원래 가려던 페이지 저장
            next_url = request.session.pop('kakao_next', None) or '/'
            request.session['profile_complete_next'] = next_url
            
            # 카카오 회원가입 정보 세션에 저장
            request.session['kakao_signup_user_id'] = user.user_id
            request.session['kakao_signup_name'] = user.name
            request.session['kakao_signup_nickname'] = user.nickname
            request.session['kakao_signup_mode'] = True
            
            # 약관 동의 페이지로 리다이렉트
            return redirect('common:terms')
        
        # 7. 세션에 로그인 정보 저장 (주소 정보가 있는 경우만)
        try:
            request.session['user_id'] = user.user_id
            request.session['user_name'] = user.name
            request.session['nickname'] = user.nickname
            request.session['is_kakao_user'] = True  # 카카오 로그인 여부 저장
            
            # 세션 만료 시간 설정 (브라우저 닫으면 만료)
            request.session.set_expiry(0)
        except Exception as e:
            messages.error(request, "세션 저장 중 오류가 발생했습니다.")
            return redirect('/login/')
        
        # 8. 관리자 체크 및 리다이렉트
        if user.manager_yn == 1:
            request.session['manager_id'] = user.member_id
            request.session['manager_name'] = user.name
            next_url = request.session.pop('kakao_next', None) or '/manager/dashboard/'
            return redirect(next_url)
        
        # 일반 사용자는 메인 페이지로
        next_url = request.session.pop('kakao_next', None) or '/'
        return redirect(next_url)
        
    except requests.RequestException as e:
        messages.error(request, f"카카오 로그인 중 네트워크 오류가 발생했습니다.")
        return redirect('/login/')
    except Exception as e:
        # 모든 예외 처리 - 무한 로딩 방지
        messages.error(request, "카카오 로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        return redirect('/login/')
# 회원 가입 부분 ----------------------------------------
USERNAME_PATTERN = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$')
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=])[A-Za-z\d!@#$%^&*()_+\-=]{8,}$'
)
PHONE_PATTERN = re.compile(r'^\d{3}-\d{4}-\d{4}$')

def signup(request):

    # 카카오 회원가입 모드 확인
    is_kakao_signup = request.session.get('kakao_signup_mode', False) or request.GET.get('kakao') == 'true'

    if request.method == "POST":
        data = request.POST
        ctx = {"input": data}

        # 카카오 회원가입인 경우 체크
        if is_kakao_signup:
            kakao_user_id = request.session.get('kakao_signup_user_id')
            if not kakao_user_id:
                messages.error(request, "카카오 회원가입 정보를 찾을 수 없습니다.")
                return redirect('/login/')

            # 입력값 가져오기
            name = data.get('name')
            nickname = data.get('nickname')
            birthday = data.get('birthday')
            gender = data.get('gender')
            address = data.get('address')
            address_detail = data.get('address_detail', '')
            address_data_str = data.get('address_data', '')
            phone = data.get('phone')

            # 닉네임 중복 체크
            if nickname and Member.objects.filter(nickname=nickname).exists():
                messages.error(request, "이미 존재하는 닉네임입니다.")
                ctx['is_kakao_signup'] = True
                ctx['kakao_user_id'] = kakao_user_id
                ctx['kakao_name'] = request.session.get('kakao_signup_name', '')
                ctx['kakao_nickname'] = request.session.get('kakao_signup_nickname', '')
                return render(request, "common/signup.html", ctx)

            if phone and not re.match(PHONE_PATTERN, phone or ""):
                messages.error(request, "전화번호는 010-0000-0000 형식으로 입력해주세요.")
                ctx['is_kakao_signup'] = True
                ctx['kakao_user_id'] = kakao_user_id
                ctx['kakao_name'] = request.session.get('kakao_signup_name', '')
                ctx['kakao_nickname'] = request.session.get('kakao_signup_nickname', '')
                return render(request, "common/signup.html", ctx)

            if phone and Member.objects.filter(phone_num=phone).exists():
                messages.error(request, "이미 등록된 전화번호입니다.")
                ctx['is_kakao_signup'] = True
                ctx['kakao_user_id'] = kakao_user_id
                ctx['kakao_name'] = request.session.get('kakao_signup_name', '')
                ctx['kakao_nickname'] = request.session.get('kakao_signup_nickname', '')
                return render(request, "common/signup.html", ctx)
            
            # 주소 파싱
            from common.utils import parse_address
            import json
            
            if address_data_str:
                try:
                    address_data = json.loads(address_data_str)
                    addr1, addr2, addr3 = parse_address(address_data, address_detail)
                except (json.JSONDecodeError, Exception):
                    addr1 = address
                    addr2 = address_detail
                    addr3 = ""
            else:
                addr1 = address
                addr2 = address_detail
                addr3 = ""
            
            # addr1 필수 입력 검증
            if not addr1 or addr1.strip() == '':
                messages.error(request, "주소를 입력해주세요.")
                ctx['is_kakao_signup'] = True
                ctx['kakao_user_id'] = kakao_user_id
                ctx['kakao_name'] = request.session.get('kakao_signup_name', '')
                ctx['kakao_nickname'] = request.session.get('kakao_signup_nickname', '')
                return render(request, "common/signup.html", ctx)
            
            gender_value = 0 if gender == "male" else 1
            
            # DB에 새로 생성 (세션에만 저장되어 있던 정보를 DB에 저장)
            kakao_id = request.session.get('kakao_id', '')
            user = Member.objects.create(
                user_id=kakao_user_id,
                name=name,
                nickname=nickname,
                password=make_password('kakao_login_no_password'),
                birthday=birthday,
                gender=gender_value,
                addr1=addr1,
                addr2=addr2,
                addr3=addr3,
                phone_num=phone,
            )
            
            # 세션 정리 및 로그인 처리
            request.session.pop('kakao_signup_mode', None)
            request.session.pop('kakao_signup_user_id', None)
            request.session.pop('kakao_signup_name', None)
            request.session.pop('kakao_signup_nickname', None)
            request.session.pop('kakao_id', None)
            
            request.session['user_id'] = user.user_id
            request.session['user_name'] = user.name
            request.session['nickname'] = user.nickname
            request.session['is_kakao_user'] = True
            
            # 원래 가려던 페이지로 리다이렉트 (있으면)
            profile_complete_next = request.session.pop('profile_complete_next', None)
            redirect_url = profile_complete_next if profile_complete_next else '/'
            
            # 회원가입 완료 alert 표시
            context = {
                'redirect_url': redirect_url,
                'is_kakao_signup': True
            }
            return render(request, 'common/signup_success.html', context)
        
        # 일반 회원가입 처리 (카카오 회원가입이 아닐 때만 실행)
        else:
            name = data.get('name')
            user_id = data.get('username')
            password = data.get('password')
            password2 = data.get('password2')
            nickname = data.get('nickname')
            birthday = data.get('birthday')
            gender = data.get('gender')
            address = data.get('address')
            address_detail = data.get('address_detail', '')
            address_data_str = data.get('address_data', '')
            phone = data.get('phone')

            if not PASSWORD_PATTERN.match(password or ""):
                messages.error(request, "비밀번호 형식이 올바르지 않습니다.")
                return render(request, "common/signup.html", ctx)

            if password != password2:
                messages.error(request, "비밀번호가 일치하지 않습니다.")
                return render(request, "common/signup.html", ctx)

            if not USERNAME_PATTERN.match(user_id or ""):
                messages.error(request, "아이디는 6자 이상, 영문+숫자 조합이어야 합니다.")
                return render(request, "common/signup.html", ctx)

            if Member.objects.filter(user_id=user_id).exists():
                messages.error(request, "이미 존재하는 아이디입니다.")
                return render(request, "common/signup.html", ctx)

            if Member.objects.filter(nickname=nickname).exists():
                messages.error(request, "이미 존재하는 닉네임입니다.")
                return render(request, "common/signup.html", ctx)

            if not PHONE_PATTERN.match(phone or ""):
                messages.error(request, "전화번호는 010-0000-0000 형식으로 입력해주세요.")
                return render(request, "common/signup.html", ctx)

            if Member.objects.filter(phone_num=phone).exists():
                messages.error(request, "이미 등록된 전화번호입니다.")
                return render(request, "common/signup.html", ctx)

            gender_value = 0 if gender == "male" else 1

            # 주소 파싱
            from common.utils import parse_address
            import json

            # 기본 문자열 분리 (레거시 대비)
            addr1 = address.split()[0]
            addr2 = address.split()[1]
            addr3 = ' '.join(address.split()[2:]) + address_detail

            if address_data_str:
                try:
                    address_data = json.loads(address_data_str)
                    addr1, addr2, addr3 = parse_address(address_data, address_detail)
                except (json.JSONDecodeError, Exception):
                    # 파싱 실패 시 기존 방식 사용
                    addr1 = address
                    addr2 = address_detail
                    addr3 = ""

            # addr1 필수 입력 검증
            if not addr1 or addr1.strip() == '':
                messages.error(request, "주소를 입력해주세요.")
                return render(request, "common/signup.html", ctx)

            Member.objects.create(
                name=name,
                user_id=user_id,
                password=make_password(password),
                nickname=nickname,
                birthday=birthday,
                gender=gender_value,
                addr1=addr1,
                addr2=addr2,
                addr3=addr3,
                phone_num=phone,
            )

            return render(request, 'common/signup_success.html')

    # GET 요청
    context = {}
    if is_kakao_signup:
        kakao_user_id = request.session.get('kakao_signup_user_id')
        if kakao_user_id:
            # 세션에서 정보 가져오기 (DB에 저장되지 않았으므로)
            kakao_name = request.session.get('kakao_signup_name', '')
            kakao_nickname = request.session.get('kakao_signup_nickname', '')
            
            context = {
                'is_kakao_signup': True,
                'kakao_user_id': kakao_user_id,
                'kakao_name': kakao_name,
                'kakao_nickname': kakao_nickname,
                'input': {
                    'name': kakao_name,
                    'username': kakao_user_id,
                    'nickname': kakao_nickname,
                    'birthday': '',
                    'gender': '',
                    'address': '',
                    'address_detail': '',
                    'phone': '',
                }
            }
    
    return render(request, "common/signup.html", context)

def check_userid(request):
    user_id = request.GET.get('username')
    exists = Member.objects.filter(user_id=user_id).exists()
    return JsonResponse({'exists': exists})

def check_nickname(request):
    nickname = request.GET.get('nickname')
    exclude_user_id = request.GET.get('exclude_user_id')  # 카카오 회원가입 모드일 때 본인 제외
    
    if exclude_user_id:
        # 카카오 회원가입 모드: 본인 제외하고 중복 체크
        exists = Member.objects.filter(nickname=nickname).exclude(user_id=exclude_user_id).exists()
    else:
        # 일반 회원가입 모드: 전체 중복 체크
        exists = Member.objects.filter(nickname=nickname).exists()
    
    return JsonResponse({'exists': exists})

def check_phone(request):
    phone = request.GET.get('phone')
    exists = Member.objects.filter(phone_num=phone).exists()
    return JsonResponse({'exists': exists})
#--------------------------------------------------------------




def find_id(request):
    if request.method == "POST":
        name = request.POST.get('name')
        birthday = request.POST.get('birthday')
        phone1 = request.POST.get('phone1')
        phone2 = request.POST.get('phone2')
        phone3 = request.POST.get('phone3')

        # 생일 검증
        if len(birthday) != 8 or not birthday.isdigit():
            return render(request, "common/findID.html", {
                "error": "생년월일은 8자리 숫자로 입력해주세요. (예: 20020528)"
            })

        # 전화번호 검증
        if (len(phone1) != 3 or not phone1.isdigit() or
            len(phone2) != 4 or not phone2.isdigit() or
            len(phone3) != 4 or not phone3.isdigit()):
            return render(request, "common/findID.html", {
                "error": "전화번호는 숫자만 입력해야 하며 3-4-4 자리여야 합니다."
            })

        # 생년월일을 DB 포맷(YYYY-MM-DD)으로 변환
        birthday_db = f"{birthday[0:4]}-{birthday[4:6]}-{birthday[6:8]}"
        
        # 전화번호를 DB 포맷(010-0000-0000)으로 변환
        phone_num = f"{phone1}-{phone2}-{phone3}"

        # DB에서 회원 정보 조회 (탈퇴하지 않은 회원만)
        try:
            user = Member.objects.get(
                name=name,
                birthday=birthday_db,
                phone_num=phone_num,
                delete_yn=0  # 탈퇴하지 않은 회원만
            )
            
            # 아이디 찾기 성공
            return render(request, 'common/findID.html', {
                "result_id": user.user_id
            })
            
        except Member.DoesNotExist:
            return render(request, "common/findID.html", {
                "error": "입력하신 정보와 일치하는 회원을 찾을 수 없습니다."
            })
        except Member.MultipleObjectsReturned:
            # 중복된 정보가 있는 경우 (이론적으로는 발생하지 않아야 함)
            # 첫 번째 회원의 아이디 반환
            user = Member.objects.filter(
                name=name,
                birthday=birthday_db,
                phone_num=phone_num,
                delete_yn=0
            ).first()
            
            if user:
                return render(request, 'common/findID.html', {
                    "result_id": user.user_id
                })
            else:
                return render(request, "common/findID.html", {
                    "error": "입력하신 정보와 일치하는 회원을 찾을 수 없습니다."
                })

    return render(request, 'common/findID.html')

def generate_random_pw(length=12):
    letters = string.ascii_letters        # ABCabc
    digits = string.digits               # 012345
    symbols = "!@#$%^&*()"
    char_set = letters + digits + symbols

    return ''.join(random.choice(char_set) for _ in range(length))


def find_pw(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        name = request.POST.get("name")
        birthday = request.POST.get("birthday")
        phone1 = request.POST.get("phone1")
        phone2 = request.POST.get("phone2")
        phone3 = request.POST.get("phone3")

        # 생년월일 검증 및 DB 포맷(YYYY-MM-DD)으로 변환
        birthday = (birthday or "").strip()
        birthday_db = None

        # 20020528 형식
        if len(birthday) == 8 and birthday.isdigit():
            birthday_db = f"{birthday[0:4]}-{birthday[4:6]}-{birthday[6:8]}"
        # 2002-05-28 형식
        elif len(birthday) == 10 and birthday.count("-") == 2:
            birthday_db = birthday
        else:
            return render(request, "common/findPW.html", {
                "error": "생년월일은 20020528 또는 2002-05-28 형식으로 입력해주세요."
            })

        # 전화번호 검증
        if (len(phone1) != 3 or not phone1.isdigit() or
            len(phone2) != 4 or not phone2.isdigit() or
            len(phone3) != 4 or not phone3.isdigit()):
            return render(request, "common/findPW.html", {
                "error": "전화번호는 3-4-4 숫자로 입력해주세요."
            })

        # DB에 저장된 형식(010-0000-0000)에 맞게 전화번호 구성
        phone_num = f"{phone1}-{phone2}-{phone3}"

        # 실제 회원 정보 확인
        try:
            user = Member.objects.get(
                user_id=user_id,
                name=name,
                birthday=birthday_db,
                phone_num=phone_num,
            )
        except Member.DoesNotExist:
            return render(request, "common/findPW.html", {
                "error": "입력하신 정보와 일치하는 회원을 찾을 수 없습니다."
            })

        # 12자리 랜덤 비밀번호 생성 및 DB 비밀번호 갱신
        new_password = generate_random_pw(12)
        user.password = make_password(new_password)
        user.save(update_fields=["password"])

        return render(request, "common/findPW.html", {
            "result_pw": new_password
        })

    return render(request, "common/findPW.html")

def terms (request):
    return render(request, "common/terms.html")