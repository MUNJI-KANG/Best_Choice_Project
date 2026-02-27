import os
import time
import json
import requests
import urllib.request
import urllib.parse
import re, time
from django.core.cache import cache
from django.shortcuts import render, redirect
from facility.utils import build_facility_queryset
from django.conf import settings
from django.contrib import messages

from facility.models import Facility
from facility.models import FacilityInfo
from member.models import Member
from common.models import AddInfo,Comment


from common.paging import pager

# 시설 api 가져오기

GEO_CACHE_TTL = 60 * 30  # 30분

FACILITY_LIST_CACHE_TTL = 60 * 5

_geo_cache = {}


def facility_list(request):
    """
    조건에 맞는 공공 체육시설 목록을 조회하고 지도 렌더링을 위한 데이터를 준비하는 뷰 함수입니다.

    [기술적 주안점]
    - 대규모 트래픽 대비 캐싱(Caching) 적용: 검색 조건(지역, 키워드)을 키(Key)로 삼아 Django Cache Framework를 적용하고 TTL(5분)을 설정하여, 반복적인 대량의 DB 조회(I/O) 부하를 획기적으로 줄였습니다.
    - 사용자 경험(UX) 최적화: 검색 조건이 없을 경우 세션의 유저 주소 정보(addr1)를 SIDO_MAP 매핑을 통해 역산하여, 사용자 맞춤형 지역 시설을 디폴트로 노출하도록 설계했습니다.
    """
    KAKAO_SCRIPT_KEY = os.getenv("KAKAO_SCRIPT_KEY")

    cp_nm = request.GET.get('cpNm')
    cpb_nm = request.GET.get('cpbNm')
    keyword = (request.GET.get('keyword') or "").strip()

    user = request.session.get("user_id")

    if not keyword:
        if not cp_nm or not cpb_nm:
            if user:
                SIDO_MAP = {
                    "서울": "서울특별시",
                    "경기": "경기도",
                    "부산": "부산광역시",
                    "대구": "대구광역시",
                    "인천": "인천광역시",
                    "광주": "광주광역시",
                    "대전": "대전광역시",
                    "울산": "울산광역시",
                    "세종": "세종특별자치시",
                    "강원": "강원도",
                    "충북": "충청북도",
                    "충남": "충청남도",
                    "전북": "전라북도",
                    "전남": "전라남도",
                    "경북": "경상북도",
                    "경남": "경상남도",
                    "제주": "제주특별자치도",
                }

                try:
                    member = Member.objects.get(user_id=user)
                    addr1_raw = (member.addr1 or "").strip()
                    if not cp_nm:
                        cp_nm = SIDO_MAP.get(addr1_raw, addr1_raw)
                    if not cpb_nm:
                        cpb_nm = (member.addr2 or "").strip()
                except Member.DoesNotExist:
                    pass

    if not keyword:
        cp_nm = cp_nm or "서울특별시"
        cpb_nm = cpb_nm or "강남구"


    cache_key = f"facility_list:{cp_nm}:{cpb_nm}:{keyword}"
    cached = cache.get(cache_key)
    if cached:
        facilities = cached

    else:
        qs = build_facility_queryset(
            cp_nm=cp_nm,
            cpb_nm=cpb_nm,
            keyword=keyword,
            public_only=True,
            normal_only=True,        # 사용자 → 정상 운영만
            exclude_registered=False # 사용자 → 전부 노출
        )

        facilities = [
            {
                "id": f.faci_cd,
                "name": f.faci_nm or "",
                "address": f.faci_road_addr or f.faci_addr or "",
                "sido": f.cp_nm or "",
                "sigungu": f.cpb_nm or "",
                "phone": f.faci_tel_no or "",
                "lat": f.faci_lat,
                "lng": f.faci_lot,
            }
            for f in qs
        ]

        info_ids = set(
            FacilityInfo.objects.values_list("facility_id", flat=True)
        )
        facilities.sort(key=lambda x: x["id"] not in info_ids)

        # 캐시 저장
        cache.set(cache_key, facilities, FACILITY_LIST_CACHE_TTL)

    per_page = int(request.GET.get("per_page", 10))
    paging = pager(request, facilities, per_page=per_page)

    page_obj = paging['page_obj']
    page_facilities = kakao_for_map(page_obj)

    context = {
        "page_obj": page_obj,
        "page_facilities": page_facilities,
        "per_page": per_page,
        "cpNm": cp_nm,
        "cpbNm": cpb_nm,
        "keyword": keyword,
        "merged_count": len(facilities),
        "block_range": paging['block_range'],
        "block_start": paging['block_start'],
        "block_end": paging['block_end'],
        "no_result": len(facilities) == 0,
        "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
    }

    return render(request, "facility/facility_list.html", context)



_geo_cache = {}
GEO_CACHE_TTL = 60 * 60 * 24  # 24시간



def clean_address(addr):
    if not addr:
        return ""

    addr = re.sub(r'\(.*?\)', '', addr)           # (목동) 제거
    addr = re.sub(r'지하?\d*층?', '', addr)        # 지하2층, 지층 제거
    addr = re.sub(r'B\d+호?', '', addr)            # B02호 제거
    addr = re.sub(r'\d+블럭', '', addr)            # 6블럭 제거
    addr = addr.replace(",", " ")

    return addr.strip()



def _get_cached_geo(address):
    entry = _geo_cache.get(address)
    if not entry:
        return None

    if time.time() - entry["ts"] > GEO_CACHE_TTL:
        _geo_cache.pop(address, None)
        return None

    return entry["coords"]


def _set_cached_geo(address, lat, lng):
    _geo_cache[address] = {
        "coords": (lat, lng),
        "ts": time.time(),
    }



def get_sigungu_center(sido, sigungu):
    """시군구 중심 좌표 가져오는 fallback"""
    query = f"{sido} {sigungu}"

    key = os.getenv("KAKAO_REST_API_KEY")
    headers = {"Authorization": f"KakaoAK {key}"}

    try:
        resp = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            params={"query": query},
            headers=headers,
            timeout=3
        )
        docs = resp.json().get("documents")
        if docs:
            return float(docs[0]["y"]), float(docs[0]["x"])

    except:
        pass

    # 최종 fallback → 서울
    return 37.5665, 126.9780



def kakao_for_map(page_obj):
    """
    시설 목록의 주소를 카카오 로컬 API를 통해 위도/경도로 변환(Geocoding)하는 함수입니다.

    [기술적 주안점]
    - API 호출 최소화 및 인메모리 캐싱: 외부 API(카카오)의 Rate Limit(호출 제한)과 네트워크 지연을 방지하기 위해, 자체적인 _geo_cache 딕셔너리와 TTL(24시간) 로직을 구현하여 중복된 주소의 API 호출을 원천 차단했습니다.
    - 무중단 Fallback 아키텍처: 지오코딩 실패나 API 장애 발생 시 에러를 뱉고 멈추지 않도록, get_sigungu_center()를 통한 시/군/구 중심 좌표 또는 서울 시청 좌표로 대체(Fallback)하여 지도 렌더링의 안정성을 보장합니다.
    """
    KAKAO_REST_KEY = os.getenv("KAKAO_REST_API_KEY")
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"} if KAKAO_REST_KEY else None

    result = []

    for fac in page_obj:
        raw_addr = fac.get("address") or ""
        clean_addr_text = clean_address(raw_addr)

        fac["full_address"] = raw_addr
        lat = None
        lng = None

        if clean_addr_text:
            cached = _get_cached_geo(clean_addr_text)
            if cached:
                lat, lng = cached

        if headers and clean_addr_text and (lat is None or lng is None):
            try:
                resp = requests.get(
                    "https://dapi.kakao.com/v2/local/search/address.json",
                    params={"query": clean_addr_text},
                    headers=headers,
                    timeout=3,
                )
                docs = resp.json().get("documents")

                if docs:
                    lat = float(docs[0]["y"])
                    lng = float(docs[0]["x"])
                    _set_cached_geo(clean_addr_text, lat, lng)

            except Exception as e:
                print("[지오코딩 오류]", e)

        if lat is None or lng is None:
            lat, lng = get_sigungu_center(fac["sido"], fac["sigungu"])

        # 최종 좌표 부여
        fac["lat"] = lat
        fac["lng"] = lng

        # 지도에 반드시 추가 → 누락되는 시설 없음!
        result.append(fac)

    return result

def facility_detail(request, fk):
    """
    특정 시설의 상세 정보, 예약 가능 여부, 첨부파일 및 댓글을 종합하여 반환하는 뷰 함수입니다.

    [기술적 주안점]
    - 이기종 데이터 병합(Data Merging): 공공데이터 원천 테이블(Facility)과 관리자가 커스텀하게 관리하는 정보 테이블(FacilityInfo)을 동시에 조회하고, 삼항 연산자를 활용해 유효한 데이터를 우선순위에 따라 매핑함으로써 완벽한 데이터 정합성을 제공합니다.
    """
    user_id = request.session.get('user_id')
    KAKAO_SCRIPT_KEY = os.getenv("KAKAO_SCRIPT_KEY")

    try:
        files = []

        facility_info = FacilityInfo.objects.filter(facility_id=fk).first()
        facility = Facility.objects.filter(faci_cd=fk).first()

        if not facility_info and not facility:
            return render(request, "facility/facility_view.html", {
                "error": "시설 정보를 찾을 수 없습니다."
            })

        r_data = {
            "id": fk,
            "name": "",
            "address": "",
            "sido": "",
            "sigungu": "",
            "phone": "",
            "homepage": "",
            "fcob_nm": "",
            "faci_stat_nm": "",
            "schk_tot_grd_nm": "",
            "lat": None,
            "lng": None,
            "image_url": "/media/uploads/facility/photo/default.png",
        }

        can_reserve = False
        can_recruit = False
        reserve_message = "해당 시설에 문의해주세요"

        if facility_info:
            r_data["name"] = facility_info.faci_nm or (facility.faci_nm if facility else "")
            r_data["address"] = facility_info.address or (facility.faci_road_addr or facility.faci_addr if facility else "")
            r_data["sido"] = facility_info.sido or (facility.cp_nm if facility else "")
            r_data["sigungu"] = facility_info.sigugun or (facility.cpb_nm if facility else "")
            r_data["phone"] = facility_info.tel or (facility.faci_tel_no if facility else "")
            r_data["homepage"] = facility_info.homepage or (facility.faci_homepage if facility else "")

            if facility_info.photo:
                r_data["image_url"] = facility_info.photo.url

            if facility_info.reservation_time:
                can_reserve = True
                reserve_message = "가능"

            can_recruit = True

            if facility:
                r_data["fcob_nm"] = facility.fcob_nm or ""
                r_data["faci_stat_nm"] = facility.faci_stat_nm or ""
                r_data["schk_tot_grd_nm"] = facility.schk_tot_grd_nm or ""
                r_data["lat"] = facility.faci_lat
                r_data["lng"] = facility.faci_lot

            add_info_objs = AddInfo.objects.filter(facility_id=facility_info.id)

            for add_info in add_info_objs:
                file_ext = os.path.splitext(add_info.path)[1].lower()
                is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

                file_data = {
                    'id': add_info.add_info_id,
                    'name': add_info.file_name,
                    'url': f"{settings.MEDIA_URL}{add_info.path}",
                    'is_image': is_image,
                }

                if not is_image:
                    files.append(file_data)
            print("files : ",files)
        else:
            r_data.update({
                "id": facility.faci_cd,
                "name": facility.faci_nm or "",
                "address": facility.faci_road_addr or facility.faci_addr or "",
                "sido": facility.cp_nm or "",
                "sigungu": facility.cpb_nm or "",
                "phone": facility.faci_tel_no or "",
                "homepage": facility.faci_homepage or "",
                "fcob_nm": facility.fcob_nm or "",
                "faci_stat_nm": facility.faci_stat_nm or "",
                "schk_tot_grd_nm": facility.schk_tot_grd_nm or "",
                "lat": facility.faci_lat,
                "lng": facility.faci_lot,
            })

            img_url = get_naver_image(r_data["name"])
            if img_url:
                r_data["image_url"] = img_url

            can_reserve = False
            can_recruit = False

        try:
            geo_fixed = kakao_for_map([r_data])[0]
            r_data["lat"] = geo_fixed["lat"]
            r_data["lng"] = geo_fixed["lng"]
        except:
            print("카카오 지오코딩 실패 → 좌표 없음")

        comment_objs = Comment.objects.select_related("member_id").filter(
            facility=fk
        ).order_by("reg_date")

        comments = []
        for c in comment_objs:
            comments.append({
                "comment_id": c.comment_id,
                "comment": c.comment,
                "author": c.member_id.nickname if hasattr(c.member_id, 'nickname') else "알 수 없음",
                "is_admin": (c.member_id.manager_yn == 1 if c.member_id else False),
                "reg_date": c.reg_date,
                "is_deleted": c.delete_date is not None,
            })

        return render(request, "facility/facility_view.html", {
            "facility": r_data,
            "files": files,
            "KAKAO_SCRIPT_KEY": KAKAO_SCRIPT_KEY,
            "can_reserve": can_reserve,
            "can_recruit": can_recruit,
            "reserve_message": reserve_message,
            "comments": comments,
            "facility_id": fk,
            "user_id": user_id,
            "comment_fk": fk,   # 댓글 URL에서 반드시 이 변수 사용
        })

    except Exception as e:
        print("[facility_detail ERROR]", e)
        import traceback
        print(traceback.format_exc())
        return render(request, "facility/facility_view.html", {
            "error": f"상세 정보를 불러오는 중 오류가 발생했습니다: {str(e)}"
        })

    
# 댓글 추가 기능
def add_comment(request, fk):
    from common.utils import check_login
    res = check_login(request)
    if res:
        return res

    if request.method != "POST":
        return redirect("facility:detail", fk=fk)

    user_id = request.session.get("user_id")
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login/")

    content = request.POST.get("content", "").strip()
    if not content:
        messages.error(request, "댓글 내용을 입력해 주세요.")
        return redirect("facility:detail", fk=fk)

    Comment.objects.create(
        facility=Facility.objects.get(faci_cd=fk),
        member_id=member,
        comment=content,
    )

    messages.success(request, "댓글이 등록되었습니다.")
    return redirect("facility:detail", fk=fk)



# 네이버 이미지로 한번 해보자

def get_naver_image(query):
    """
    시설의 등록된 사진이 없을 경우, 네이버 이미지 검색 API를 호출하여 대체 이미지를 동적으로 수집하는 함수입니다.

    [기술적 주안점]
    - 동적 콘텐츠 수집 및 예외 처리: urllib를 활용한 외부 Open API 통신 시 timeout(3초)을 명시적으로 설정하여 서버가 무한 대기(Hang)에 빠지는 것을 방지하고, 검색 결과가 없거나 예외 발생 시 시스템 에러 없이 None을 반환하여 유연하게 대처했습니다.
    """
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ 네이버 API 키 없음")
        return None

    # 검색어 인코딩
    enc_query = urllib.parse.quote(query)

    url = f"https://openapi.naver.com/v1/search/image?query={enc_query}&display=1&sort=sim"

    # 요청 객체 생성
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

    try:
        response = urllib.request.urlopen(req, timeout=3)
        rescode = response.getcode()

        if rescode == 200:
            response_body = response.read().decode('utf-8')
            data = json.loads(response_body)

            items = data.get("items")
            if not items:
                print("❌ 네이버 이미지 없음:", query)
                return None

            # 가장 첫 번째 이미지 링크 반환
            return items[0].get("link")
        else:
            print("네이버 API 오류코드:", rescode)
            return None

    except Exception as e:
        print("네이버 이미지 검색 오류:", e)
        return None

 